from flask import Blueprint, render_template, request, jsonify, Response
from flask_login import login_required, current_user
from app.models import db, Camera, Detection
from app.services.camera_service import CameraService
from app.services.ml_service import MLService
from datetime import datetime
import cv2
import numpy as np
import base64

bp = Blueprint('camera', __name__, url_prefix='/camera')
camera_service = CameraService()
ml_service = MLService()

@bp.route('/')
@login_required
def index():
    cameras = Camera.query.filter_by(user_id=current_user.id).all()
    return render_template('camera.html', cameras=cameras)

@bp.route('/add', methods=['POST'])
@login_required
def add_camera():
    data = request.get_json()
    
    name = data.get('name', '').strip()
    location = data.get('location', '').strip()
    
    if not name:
        return jsonify({'success': False, 'error': 'Camera name is required'}), 400
    
    camera = Camera(
        user_id=current_user.id,
        name=name,
        location=location,
        is_active=True
    )
    
    db.session.add(camera)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'camera': {
            'id': camera.id,
            'name': camera.name,
            'location': camera.location,
            'is_active': camera.is_active
        }
    })

@bp.route('/<int:camera_id>/update', methods=['PUT'])
@login_required
def update_camera(camera_id):
    camera = Camera.query.filter_by(id=camera_id, user_id=current_user.id).first()
    
    if not camera:
        return jsonify({'success': False, 'error': 'Camera not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        camera.name = data['name']
    if 'location' in data:
        camera.location = data['location']
    if 'is_active' in data:
        camera.is_active = data['is_active']
    if 'motion_enabled' in data:
        camera.motion_enabled = data['motion_enabled']
    if 'object_detection_enabled' in data:
        camera.object_detection_enabled = data['object_detection_enabled']
    if 'face_detection_enabled' in data:
        camera.face_detection_enabled = data['face_detection_enabled']
    
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/<int:camera_id>/delete', methods=['DELETE'])
@login_required
def delete_camera(camera_id):
    camera = Camera.query.filter_by(id=camera_id, user_id=current_user.id).first()
    
    if not camera:
        return jsonify({'success': False, 'error': 'Camera not found'}), 404
    
    db.session.delete(camera)
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/<int:camera_id>/process-frame', methods=['POST'])
@login_required
def process_frame(camera_id):
    camera = Camera.query.filter_by(id=camera_id, user_id=current_user.id).first()
    
    if not camera:
        return jsonify({'success': False, 'error': 'Camera not found'}), 404
    
    data = request.get_json()
    frame_data = data.get('frame')
    
    if not frame_data:
        return jsonify({'success': False, 'error': 'No frame data'}), 400
    
    try:
        frame_bytes = base64.b64decode(frame_data.split(',')[1])
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        results = {
            'motion': False,
            'objects': [],
            'faces': [],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if camera.motion_enabled:
            motion_detected = camera_service.detect_motion(camera_id, frame)
            results['motion'] = motion_detected
            
            if motion_detected:
                camera.last_motion = datetime.utcnow()
        
        if camera.object_detection_enabled:
            objects = ml_service.detect_objects(frame)
            results['objects'] = objects
            
            for obj in objects:
                detection = Detection(
                    camera_id=camera_id,
                    detection_type='object',
                    object_class=obj['class'],
                    confidence=obj['confidence'],
                    bbox_x=obj['bbox'][0],
                    bbox_y=obj['bbox'][1],
                    bbox_width=obj['bbox'][2],
                    bbox_height=obj['bbox'][3]
                )
                db.session.add(detection)
        
        if camera.face_detection_enabled:
            faces = ml_service.detect_faces(frame)
            results['faces'] = faces
            
            for face in faces:
                detection = Detection(
                    camera_id=camera_id,
                    detection_type='face',
                    confidence=face['confidence'],
                    bbox_x=face['bbox'][0],
                    bbox_y=face['bbox'][1],
                    bbox_width=face['bbox'][2],
                    bbox_height=face['bbox'][3]
                )
                db.session.add(detection)
        
        camera.last_detection = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/<int:camera_id>/detections')
@login_required
def get_detections(camera_id):
    camera = Camera.query.filter_by(id=camera_id, user_id=current_user.id).first()
    
    if not camera:
        return jsonify({'success': False, 'error': 'Camera not found'}), 404
    
    limit = request.args.get('limit', 50, type=int)
    
    detections = Detection.query.filter_by(camera_id=camera_id)\
        .order_by(Detection.timestamp.desc())\
        .limit(limit)\
        .all()
    
    results = []
    for detection in detections:
        results.append({
            'id': detection.id,
            'type': detection.detection_type,
            'class': detection.object_class,
            'confidence': detection.confidence,
            'bbox': [detection.bbox_x, detection.bbox_y, detection.bbox_width, detection.bbox_height],
            'timestamp': detection.timestamp.isoformat()
        })
    
    return jsonify({
        'success': True,
        'detections': results
    })

@bp.route('/<int:camera_id>/stats')
@login_required
def get_stats(camera_id):
    camera = Camera.query.filter_by(id=camera_id, user_id=current_user.id).first()
    
    if not camera:
        return jsonify({'success': False, 'error': 'Camera not found'}), 404
    
    total_detections = Detection.query.filter_by(camera_id=camera_id).count()
    
    object_detections = Detection.query.filter_by(camera_id=camera_id, detection_type='object').count()
    
    face_detections = Detection.query.filter_by(camera_id=camera_id, detection_type='face').count()
    
    return jsonify({
        'success': True,
        'stats': {
            'total_detections': total_detections,
            'object_detections': object_detections,
            'face_detections': face_detections,
            'last_motion': camera.last_motion.isoformat() if camera.last_motion else None,
            'last_detection': camera.last_detection.isoformat() if camera.last_detection else None
        }
    })
