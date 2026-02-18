"""
Entry Logs Routes
Handles entry history viewing and entry approval/denial
"""

from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from datetime import datetime, timezone
import logging

from app.models import AccessLog, Camera, FacePerson, db

bp = Blueprint('entries', __name__, url_prefix='/entries')
logger = logging.getLogger(__name__)


@bp.route('/')
@login_required
def index():
    """Render the entry history page"""
    return render_template('entries.html')


@bp.route('/list', methods=['GET'])
@login_required
def list_entries():
    """
    Get paginated entry logs for the current user's cameras
    
    Query params:
        camera_id: int (optional) — filter by camera
        is_known: bool (optional) — filter by known/unknown
        action: str (optional) — filter by action type
        limit: int (default: 50)
        offset: int (default: 0)
    """
    try:
        camera_id = request.args.get('camera_id', type=int)
        is_known = request.args.get('is_known', type=str)
        action = request.args.get('action', type=str)
        limit = min(request.args.get('limit', 50, type=int), 200)
        offset = request.args.get('offset', 0, type=int)
        
        # Base query: only entries from user's cameras
        query = db.session.query(AccessLog).join(Camera).filter(
            Camera.user_id == current_user.id
        )
        
        # Apply filters
        if camera_id:
            query = query.filter(AccessLog.camera_id == camera_id)
        
        if is_known is not None:
            if is_known.lower() == 'true':
                query = query.filter(AccessLog.is_known == True)
            elif is_known.lower() == 'false':
                query = query.filter(AccessLog.is_known == False)
        
        if action:
            query = query.filter(AccessLog.action == action)
        
        total = query.count()
        entries = query.order_by(AccessLog.timestamp.desc()).offset(offset).limit(limit).all()
        
        entries_data = [
            {
                'id': entry.id,
                'camera_id': entry.camera_id,
                'camera_name': entry.camera.name if entry.camera else 'Unknown',
                'person_id': entry.person_id,
                'person_name': entry.person_name or 'Unknown',
                'is_known': entry.is_known,
                'confidence': round(entry.confidence, 2) if entry.confidence else 0.0,
                'image_path': entry.image_path,
                'firebase_image_url': entry.firebase_image_url,
                'access_granted': entry.access_granted,
                'action': entry.action,
                'approved_by': entry.approved_by,
                'firebase_id': entry.firebase_id,
                'timestamp': entry.timestamp.isoformat() if entry.timestamp else None
            }
            for entry in entries
        ]
        
        return jsonify({
            'success': True,
            'total': total,
            'entries': entries_data,
            'has_more': (offset + limit) < total
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching entries: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@bp.route('/approve/<int:entry_id>', methods=['POST'])
@login_required
def approve_entry(entry_id):
    """
    Approve a pending entry — opens the door
    
    POST /entries/approve/<entry_id>
    """
    try:
        entry = db.session.query(AccessLog).join(Camera).filter(
            AccessLog.id == entry_id,
            Camera.user_id == current_user.id
        ).first()
        
        if not entry:
            return jsonify({'success': False, 'message': 'Entry not found'}), 404
        
        if entry.action not in ['pending_approval', 'alert_sent']:
            return jsonify({'success': False, 'message': f'Entry cannot be approved (current action: {entry.action})'}), 400
        
        # Update entry
        entry.action = 'door_opened'
        entry.access_granted = True
        entry.approved_by = current_user.id
        
        # Attempt to open the door
        try:
            from app.services.door_control_service import DoorControlService
            door_service = DoorControlService()
            door_service.approve_entry(entry.camera_id, current_user.username)
        except Exception as e:
            logger.warning(f"Door control not available: {e}")
        
        # Update Firebase
        try:
            from app.services.firebase_service import FirebaseService
            firebase = FirebaseService()
            firebase.update_entry_action(entry.firebase_id, 'door_opened', current_user.username)
        except Exception as e:
            logger.warning(f"Firebase update failed: {e}")
        
        # Send notification
        try:
            from app.services.notification_service import NotificationService
            notif_service = NotificationService()
            notif_service.send_door_action_notification(
                'door_opened', entry.person_name, entry.camera_id, current_user.username
            )
        except Exception as e:
            logger.warning(f"Notification failed: {e}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Entry approved for {entry.person_name}. Door opened.',
            'entry': {
                'id': entry.id,
                'action': entry.action,
                'access_granted': entry.access_granted,
                'approved_by': current_user.username
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error approving entry: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@bp.route('/deny/<int:entry_id>', methods=['POST'])
@login_required
def deny_entry(entry_id):
    """
    Deny a pending entry — keeps door locked
    
    POST /entries/deny/<entry_id>
    """
    try:
        entry = db.session.query(AccessLog).join(Camera).filter(
            AccessLog.id == entry_id,
            Camera.user_id == current_user.id
        ).first()
        
        if not entry:
            return jsonify({'success': False, 'message': 'Entry not found'}), 404
        
        if entry.action not in ['pending_approval', 'alert_sent']:
            return jsonify({'success': False, 'message': f'Entry cannot be denied (current action: {entry.action})'}), 400
        
        # Update entry
        entry.action = 'entry_denied'
        entry.access_granted = False
        entry.approved_by = current_user.id
        
        # Update Firebase
        try:
            from app.services.firebase_service import FirebaseService
            firebase = FirebaseService()
            firebase.update_entry_action(entry.firebase_id, 'entry_denied', current_user.username)
        except Exception as e:
            logger.warning(f"Firebase update failed: {e}")
        
        # Send notification
        try:
            from app.services.notification_service import NotificationService
            notif_service = NotificationService()
            notif_service.send_door_action_notification(
                'entry_denied', entry.person_name, entry.camera_id, current_user.username
            )
        except Exception as e:
            logger.warning(f"Notification failed: {e}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Entry denied for {entry.person_name}. Door remains locked.',
            'entry': {
                'id': entry.id,
                'action': entry.action,
                'access_granted': entry.access_granted
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error denying entry: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@bp.route('/stats', methods=['GET'])
@login_required
def entry_stats():
    """Get entry statistics for the current user"""
    try:
        from sqlalchemy import func
        from datetime import timedelta
        
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        
        # Base query
        base_q = db.session.query(AccessLog).join(Camera).filter(
            Camera.user_id == current_user.id
        )
        
        # Today's stats
        today_q = base_q.filter(AccessLog.timestamp >= today_start)
        today_total = today_q.count()
        today_known = today_q.filter(AccessLog.is_known == True).count()
        today_unknown = today_q.filter(AccessLog.is_known == False).count()
        today_granted = today_q.filter(AccessLog.access_granted == True).count()
        
        # Pending approvals
        pending = base_q.filter(AccessLog.action.in_(['pending_approval', 'alert_sent'])).count()
        
        # This week
        week_total = base_q.filter(AccessLog.timestamp >= week_start).count()
        
        # All-time
        all_total = base_q.count()
        
        return jsonify({
            'success': True,
            'stats': {
                'today': {
                    'total': today_total,
                    'known': today_known,
                    'unknown': today_unknown,
                    'access_granted': today_granted
                },
                'pending_approvals': pending,
                'this_week': week_total,
                'all_time': all_total
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching entry stats: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
