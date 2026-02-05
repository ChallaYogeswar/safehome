from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Camera, Detection, Alert
from datetime import datetime, timedelta
from sqlalchemy import func

bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@bp.route('/')
@login_required
def index():
    return render_template('analytics.html')

@bp.route('/detections')
@login_required
def detection_analytics():
    days = request.args.get('days', 7, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    daily_detections = db.session.query(
        func.date(Detection.timestamp).label('date'),
        func.count(Detection.id).label('count')
    ).join(Camera).filter(
        Camera.user_id == current_user.id,
        Detection.timestamp >= start_date
    ).group_by('date').all()
    
    detections_by_type = db.session.query(
        Detection.detection_type,
        func.count(Detection.id).label('count')
    ).join(Camera).filter(
        Camera.user_id == current_user.id,
        Detection.timestamp >= start_date
    ).group_by(Detection.detection_type).all()
    
    top_objects = db.session.query(
        Detection.object_class,
        func.count(Detection.id).label('count')
    ).join(Camera).filter(
        Camera.user_id == current_user.id,
        Detection.detection_type == 'object',
        Detection.timestamp >= start_date
    ).group_by(Detection.object_class)\
     .order_by(func.count(Detection.id).desc())\
     .limit(10).all()
    
    return jsonify({
        'success': True,
        'daily_detections': [{'date': str(d[0]), 'count': d[1]} for d in daily_detections],
        'detections_by_type': [{'type': t[0], 'count': t[1]} for t in detections_by_type],
        'top_objects': [{'class': o[0], 'count': o[1]} for o in top_objects if o[0]]
    })

@bp.route('/alerts')
@login_required
def alert_analytics():
    days = request.args.get('days', 7, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    daily_alerts = db.session.query(
        func.date(Alert.created_at).label('date'),
        func.count(Alert.id).label('count')
    ).filter(
        Alert.user_id == current_user.id,
        Alert.created_at >= start_date
    ).group_by('date').all()
    
    alerts_by_severity = db.session.query(
        Alert.severity,
        func.count(Alert.id).label('count')
    ).filter(
        Alert.user_id == current_user.id,
        Alert.created_at >= start_date
    ).group_by(Alert.severity).all()
    
    alerts_by_type = db.session.query(
        Alert.alert_type,
        func.count(Alert.id).label('count')
    ).filter(
        Alert.user_id == current_user.id,
        Alert.created_at >= start_date
    ).group_by(Alert.alert_type).all()
    
    return jsonify({
        'success': True,
        'daily_alerts': [{'date': str(d[0]), 'count': d[1]} for d in daily_alerts],
        'alerts_by_severity': [{'severity': s[0], 'count': s[1]} for s in alerts_by_severity],
        'alerts_by_type': [{'type': t[0], 'count': t[1]} for t in alerts_by_type]
    })

@bp.route('/cameras')
@login_required
def camera_analytics():
    cameras = Camera.query.filter_by(user_id=current_user.id).all()
    
    camera_stats = []
    for camera in cameras:
        total_detections = Detection.query.filter_by(camera_id=camera.id).count()
        
        last_24h = Detection.query.filter(
            Detection.camera_id == camera.id,
            Detection.timestamp >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        camera_stats.append({
            'id': camera.id,
            'name': camera.name,
            'location': camera.location,
            'total_detections': total_detections,
            'last_24h_detections': last_24h,
            'last_motion': camera.last_motion.isoformat() if camera.last_motion else None,
            'is_active': camera.is_active
        })
    
    return jsonify({
        'success': True,
        'cameras': camera_stats
    })

@bp.route('/timeline')
@login_required
def timeline():
    hours = request.args.get('hours', 24, type=int)
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    detections = Detection.query.join(Camera).filter(
        Camera.user_id == current_user.id,
        Detection.timestamp >= start_time
    ).order_by(Detection.timestamp.desc()).limit(100).all()
    
    alerts = Alert.query.filter(
        Alert.user_id == current_user.id,
        Alert.created_at >= start_time
    ).order_by(Alert.created_at.desc()).limit(100).all()
    
    timeline_events = []
    
    for detection in detections:
        timeline_events.append({
            'type': 'detection',
            'detection_type': detection.detection_type,
            'object_class': detection.object_class,
            'confidence': detection.confidence,
            'camera_name': detection.camera.name,
            'timestamp': detection.timestamp.isoformat()
        })
    
    for alert in alerts:
        timeline_events.append({
            'type': 'alert',
            'alert_type': alert.alert_type,
            'severity': alert.severity,
            'title': alert.title,
            'timestamp': alert.created_at.isoformat()
        })
    
    timeline_events.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify({
        'success': True,
        'events': timeline_events[:100]
    })
