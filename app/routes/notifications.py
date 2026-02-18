"""
Notification Routes
Handles device token registration and notification preferences
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timezone
import logging

from app.models import DeviceToken, db

bp = Blueprint('notifications', __name__, url_prefix='/notifications')
logger = logging.getLogger(__name__)


@bp.route('/register-device', methods=['POST'])
@login_required
def register_device():
    """
    Register a device token for push notifications
    
    POST /notifications/register-device
    JSON:
        token: str (required) — FCM device token
        device_type: str (optional) — 'ios', 'android', 'web'
        device_name: str (optional) — friendly device name
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('token'):
            return jsonify({'success': False, 'message': 'Device token required'}), 400
        
        token = data['token']
        device_type = data.get('device_type', 'web')
        device_name = data.get('device_name', f"{device_type} device")
        
        # Check if token already exists
        existing = DeviceToken.query.filter_by(token=token).first()
        
        if existing:
            # Update existing token
            existing.user_id = current_user.id
            existing.device_type = device_type
            existing.device_name = device_name
            existing.is_active = True
            existing.last_used = datetime.now(timezone.utc)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Device token updated',
                'device_id': existing.id
            }), 200
        
        # Create new token
        device_token = DeviceToken(
            user_id=current_user.id,
            token=token,
            device_type=device_type,
            device_name=device_name,
            is_active=True,
            last_used=datetime.now(timezone.utc)
        )
        db.session.add(device_token)
        db.session.commit()
        
        logger.info(f"Device token registered for user {current_user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Device token registered successfully',
            'device_id': device_token.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering device token: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@bp.route('/unregister-device', methods=['DELETE'])
@login_required
def unregister_device():
    """
    Unregister a device token
    
    DELETE /notifications/unregister-device
    JSON:
        token: str (required) — FCM device token to remove
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('token'):
            return jsonify({'success': False, 'message': 'Device token required'}), 400
        
        token = data['token']
        device = DeviceToken.query.filter_by(
            token=token,
            user_id=current_user.id
        ).first()
        
        if not device:
            return jsonify({'success': False, 'message': 'Device token not found'}), 404
        
        device.is_active = False
        db.session.commit()
        
        logger.info(f"Device token unregistered for user {current_user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Device token unregistered successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error unregistering device token: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@bp.route('/devices', methods=['GET'])
@login_required
def list_devices():
    """Get all registered devices for the current user"""
    try:
        devices = DeviceToken.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).all()
        
        return jsonify({
            'success': True,
            'devices': [
                {
                    'id': d.id,
                    'device_type': d.device_type,
                    'device_name': d.device_name,
                    'is_active': d.is_active,
                    'registered_at': d.created_at.isoformat() if d.created_at else None,
                    'last_used': d.last_used.isoformat() if d.last_used else None
                }
                for d in devices
            ]
        }), 200
    
    except Exception as e:
        logger.error(f"Error listing devices: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@bp.route('/test', methods=['POST'])
@login_required
def test_notification():
    """Send a test notification to all user's devices"""
    try:
        from app.services.notification_service import NotificationService
        
        notif_service = NotificationService()
        
        # Get user's tokens
        tokens = [
            dt.token for dt in DeviceToken.query.filter_by(
                user_id=current_user.id,
                is_active=True
            ).all()
        ]
        
        if not tokens:
            return jsonify({
                'success': False,
                'message': 'No registered devices found. Register a device first.'
            }), 400
        
        from app.services.firebase_service import FirebaseService
        firebase = FirebaseService()
        
        response = firebase.send_push_notification(tokens, {
            'title': '🔔 SafeHome Test',
            'body': f'Test notification sent successfully at {datetime.now().strftime("%I:%M %p")}',
            'data': {'type': 'test'}
        })
        
        if response:
            return jsonify({
                'success': True,
                'message': f'Test notification sent to {len(tokens)} device(s)',
                'success_count': response.success_count if response else 0
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send test notification. Check Firebase configuration.'
            }), 500
    
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
