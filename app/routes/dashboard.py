from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models import Camera, Alert, Detection, AutomationRule, db
from datetime import datetime, timedelta, timezone
from sqlalchemy import func

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def index():
    cameras_count = Camera.query.filter_by(user_id=current_user.id).count()
    active_cameras = Camera.query.filter_by(user_id=current_user.id, is_active=True).count()
    
    unread_alerts = Alert.query.filter_by(user_id=current_user.id, is_read=False).count()
    
    active_rules = AutomationRule.query.filter_by(user_id=current_user.id, is_active=True).count()
    
    recent_alerts = Alert.query.filter_by(user_id=current_user.id)\
        .order_by(Alert.created_at.desc())\
        .limit(10)\
        .all()
    
    return render_template('dashboard.html',
                         cameras_count=cameras_count,
                         active_cameras=active_cameras,
                         unread_alerts=unread_alerts,
                         active_rules=active_rules,
                         recent_alerts=recent_alerts)

@bp.route('/stats')
@login_required
def stats():
    now = datetime.now(timezone.utc)
    
    stats_24h = {
        'detections': Detection.query.join(Camera).filter(
            Camera.user_id == current_user.id,
            Detection.timestamp >= now - timedelta(hours=24)
        ).count(),
        'alerts': Alert.query.filter(
            Alert.user_id == current_user.id,
            Alert.created_at >= now - timedelta(hours=24)
        ).count(),
        'motion_events': Detection.query.join(Camera).filter(
            Camera.user_id == current_user.id,
            Detection.detection_type == 'motion',
            Detection.timestamp >= now - timedelta(hours=24)
        ).count()
    }
    
    hourly_detections = db.session.query(
        func.strftime('%H', Detection.timestamp).label('hour'),
        func.count(Detection.id).label('count')
    ).join(Camera).filter(
        Camera.user_id == current_user.id,
        Detection.timestamp >= now - timedelta(hours=24)
    ).group_by('hour').all()
    
    detection_by_type = db.session.query(
        Detection.detection_type,
        func.count(Detection.id).label('count')
    ).join(Camera).filter(
        Camera.user_id == current_user.id,
        Detection.timestamp >= now - timedelta(days=7)
    ).group_by(Detection.detection_type).all()
    
    return jsonify({
        'success': True,
        'stats_24h': stats_24h,
        'hourly_detections': [{'hour': h[0], 'count': h[1]} for h in hourly_detections],
        'detection_by_type': [{'type': t[0], 'count': t[1]} for t in detection_by_type]
    })
