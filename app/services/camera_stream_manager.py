"""
Mobile & Multi-Camera Integration Service
Handles WebRTC signaling, multiple camera streams, and real-time frame processing
"""

from flask_socketio import emit, join_room, leave_room
import base64
import io
from PIL import Image
import json
from datetime import datetime, timezone
from app.models import Camera, db

class CameraStreamManager:
    """Manages camera streams and WebRTC connections"""
    
    # Store active streams: {camera_id: {user_id, type, connected_clients}}
    active_streams = {}
    
    # Store WebRTC peer connections: {camera_id: {peer_data}}
    peer_connections = {}
    
    @staticmethod
    def register_camera_stream(camera_id: int, user_id: int, stream_type: str = 'mobile'):
        """
        Register a camera stream (mobile or remote)
        stream_type: 'mobile', 'rtsp', 'http', 'mjpeg'
        """
        CameraStreamManager.active_streams[camera_id] = {
            'user_id': user_id,
            'type': stream_type,
            'connected_clients': set(),
            'registered_at': datetime.now(timezone.utc).isoformat(),
            'frame_count': 0,
            'last_frame': None
        }
        return True
    
    @staticmethod
    def unregister_camera_stream(camera_id: int):
        """Unregister a camera stream"""
        if camera_id in CameraStreamManager.active_streams:
            del CameraStreamManager.active_streams[camera_id]
        if camera_id in CameraStreamManager.peer_connections:
            del CameraStreamManager.peer_connections[camera_id]
        return True
    
    @staticmethod
    def add_stream_client(camera_id: int, client_id: str):
        """Add a client viewing this stream"""
        if camera_id in CameraStreamManager.active_streams:
            CameraStreamManager.active_streams[camera_id]['connected_clients'].add(client_id)
    
    @staticmethod
    def remove_stream_client(camera_id: int, client_id: str):
        """Remove a client from stream"""
        if camera_id in CameraStreamManager.active_streams:
            CameraStreamManager.active_streams[camera_id]['connected_clients'].discard(client_id)
    
    @staticmethod
    def get_active_streams(user_id: int = None) -> list:
        """Get list of active streams, optionally filtered by user"""
        streams = []
        for camera_id, stream_info in CameraStreamManager.active_streams.items():
            if user_id is None or stream_info['user_id'] == user_id:
                streams.append({
                    'camera_id': camera_id,
                    'type': stream_info['type'],
                    'connected_clients': len(stream_info['connected_clients']),
                    'registered_at': stream_info['registered_at'],
                    'frame_count': stream_info['frame_count']
                })
        return streams
    
    @staticmethod
    def process_frame(camera_id: int, frame_data: str) -> dict:
        """
        Process camera frame for recognition
        frame_data: base64 encoded image
        """
        try:
            # Decode base64 frame
            if frame_data.startswith('data:image'):
                frame_data = frame_data.split(',')[1]
            
            image_bytes = base64.b64decode(frame_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Update frame count
            if camera_id in CameraStreamManager.active_streams:
                CameraStreamManager.active_streams[camera_id]['frame_count'] += 1
                CameraStreamManager.active_streams[camera_id]['last_frame'] = datetime.now(timezone.utc).isoformat()
            
            return {
                'success': True,
                'image': image,
                'size': image.size
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Frame processing error: {str(e)}'
            }
    
    @staticmethod
    def store_webrtc_offer(camera_id: int, offer_sdp: str) -> str:
        """Store WebRTC offer and generate connection ID"""
        if camera_id not in CameraStreamManager.peer_connections:
            CameraStreamManager.peer_connections[camera_id] = {}
        
        connection_id = f"{camera_id}_{datetime.now(timezone.utc).timestamp()}"
        CameraStreamManager.peer_connections[camera_id][connection_id] = {
            'offer': offer_sdp,
            'answer': None,
            'candidates': [],
            'state': 'pending'
        }
        return connection_id
    
    @staticmethod
    def store_webrtc_answer(camera_id: int, connection_id: str, answer_sdp: str):
        """Store WebRTC answer"""
        if camera_id in CameraStreamManager.peer_connections:
            if connection_id in CameraStreamManager.peer_connections[camera_id]:
                CameraStreamManager.peer_connections[camera_id][connection_id]['answer'] = answer_sdp
                CameraStreamManager.peer_connections[camera_id][connection_id]['state'] = 'connected'
    
    @staticmethod
    def add_ice_candidate(camera_id: int, connection_id: str, candidate: dict):
        """Add ICE candidate for peer connection"""
        if camera_id in CameraStreamManager.peer_connections:
            if connection_id in CameraStreamManager.peer_connections[camera_id]:
                CameraStreamManager.peer_connections[camera_id][connection_id]['candidates'].append(candidate)


def register_camera_socketio_handlers(socketio):
    """Register Socket.IO handlers for camera streaming"""
    
    @socketio.on('camera:register')
    def handle_camera_register(data):
        """Mobile camera registers with server"""
        try:
            camera_id = data.get('camera_id')
            user_id = data.get('user_id')
            stream_type = data.get('stream_type', 'mobile')
            
            # Verify camera ownership
            camera = Camera.query.filter_by(id=camera_id, user_id=user_id).first()
            if not camera:
                emit('error', {'message': 'Camera not found'})
                return
            
            # Register stream
            CameraStreamManager.register_camera_stream(camera_id, user_id, stream_type)
            join_room(f'camera_{camera_id}')
            
            emit('camera:registered', {
                'camera_id': camera_id,
                'status': 'connected',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            emit('error', {'message': f'Registration error: {str(e)}'})
    
    @socketio.on('camera:disconnect')
    def handle_camera_disconnect(data):
        """Mobile camera disconnects"""
        try:
            camera_id = data.get('camera_id')
            CameraStreamManager.unregister_camera_stream(camera_id)
            leave_room(f'camera_{camera_id}')
            emit('camera:disconnected', {'camera_id': camera_id})
        except Exception as e:
            emit('error', {'message': f'Disconnect error: {str(e)}'})
    
    @socketio.on('camera:frame')
    def handle_camera_frame(data):
        """Receive frame from mobile camera"""
        try:
            camera_id = data.get('camera_id')
            frame_data = data.get('frame')
            
            if not camera_id or not frame_data:
                emit('error', {'message': 'Missing camera_id or frame'})
                return
            
            # Process frame
            result = CameraStreamManager.process_frame(camera_id, frame_data)
            
            if result['success']:
                # Broadcast frame to all viewers of this camera
                socketio.emit('camera:frame', {
                    'camera_id': camera_id,
                    'frame': frame_data,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }, room=f'camera_{camera_id}')
            else:
                emit('error', {'message': result.get('error')})
        except Exception as e:
            emit('error', {'message': f'Frame handling error: {str(e)}'})
    
    @socketio.on('camera:watch')
    def handle_camera_watch(data):
        """Client wants to watch a camera stream"""
        try:
            camera_id = data.get('camera_id')
            user_id = data.get('user_id')
            
            # Verify access
            camera = Camera.query.filter_by(id=camera_id, user_id=user_id).first()
            if not camera:
                emit('error', {'message': 'Camera not found or access denied'})
                return
            
            join_room(f'camera_{camera_id}')
            CameraStreamManager.add_stream_client(camera_id, request.sid)
            
            emit('camera:watching', {
                'camera_id': camera_id,
                'status': 'watching'
            })
        except Exception as e:
            emit('error', {'message': f'Watch error: {str(e)}'})
    
    @socketio.on('camera:unwatch')
    def handle_camera_unwatch(data):
        """Client stops watching a camera stream"""
        try:
            camera_id = data.get('camera_id')
            leave_room(f'camera_{camera_id}')
            CameraStreamManager.remove_stream_client(camera_id, request.sid)
            emit('camera:unwatching', {'camera_id': camera_id})
        except Exception as e:
            emit('error', {'message': f'Unwatch error: {str(e)}'})
    
    @socketio.on('webrtc:offer')
    def handle_webrtc_offer(data):
        """Handle WebRTC offer from mobile camera"""
        try:
            camera_id = data.get('camera_id')
            offer_sdp = data.get('offer')
            
            connection_id = CameraStreamManager.store_webrtc_offer(camera_id, offer_sdp)
            
            # Broadcast offer to all viewers
            socketio.emit('webrtc:offer', {
                'camera_id': camera_id,
                'connection_id': connection_id,
                'offer': offer_sdp
            }, room=f'camera_{camera_id}')
        except Exception as e:
            emit('error', {'message': f'WebRTC offer error: {str(e)}'})
    
    @socketio.on('webrtc:answer')
    def handle_webrtc_answer(data):
        """Handle WebRTC answer from viewer"""
        try:
            camera_id = data.get('camera_id')
            connection_id = data.get('connection_id')
            answer_sdp = data.get('answer')
            
            CameraStreamManager.store_webrtc_answer(camera_id, connection_id, answer_sdp)
            
            # Send answer back to camera
            socketio.emit('webrtc:answer', {
                'connection_id': connection_id,
                'answer': answer_sdp
            }, room=f'camera_{camera_id}')
        except Exception as e:
            emit('error', {'message': f'WebRTC answer error: {str(e)}'})
    
    @socketio.on('webrtc:candidate')
    def handle_ice_candidate(data):
        """Handle ICE candidate exchange"""
        try:
            camera_id = data.get('camera_id')
            connection_id = data.get('connection_id')
            candidate = data.get('candidate')
            
            CameraStreamManager.add_ice_candidate(camera_id, connection_id, candidate)
            
            # Broadcast candidate to all viewers
            socketio.emit('webrtc:candidate', {
                'connection_id': connection_id,
                'candidate': candidate
            }, room=f'camera_{camera_id}')
        except Exception as e:
            emit('error', {'message': f'ICE candidate error: {str(e)}'})

