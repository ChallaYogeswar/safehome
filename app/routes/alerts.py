from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room
from app import socketio
from app.models import db, Alert
from app.services.alert_service import AlertService
from datetime import datetime

bp = Blueprint('alerts', __name__, url_prefix='/alerts')
alert_service = AlertService()

@bp.route('/')
@login_required
def index():
    alerts = Alert.query.filter_by(user_id=current_user.id)\
        .order_by(Alert.created_at.desc())\
        .limit(100)\
        .all()
    
    return render_template('alerts.html', alerts=alerts)

@bp.route('/unread')
@login_required
def get_unread():
    alerts = Alert.query.filter_by(user_id=current_user.id, is_read=False)\
        .order_by(Alert.created_at.desc())\
        .all()
    
    result = []
    for alert in alerts:
        result.append({
            'id': alert.id,
            'type': alert.alert_type,
            'severity': alert.severity,
            'title': alert.title,
            'message': alert.message,
            'source': alert.source,
            'created_at': alert.created_at.isoformat()
        })
    
    return jsonify({'success': True, 'alerts': result})

@bp.route('/<int:alert_id>/read', methods=['POST'])
@login_required
def mark_read(alert_id):
    alert = Alert.query.filter_by(id=alert_id, user_id=current_user.id).first()
    
    if not alert:
        return jsonify({'success': False, 'error': 'Alert not found'}), 404
    
    alert.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/<int:alert_id>/acknowledge', methods=['POST'])
@login_required
def acknowledge(alert_id):
    alert = Alert.query.filter_by(id=alert_id, user_id=current_user.id).first()
    
    if not alert:
        return jsonify({'success': False, 'error': 'Alert not found'}), 404
    
    alert.is_acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/<int:alert_id>/delete', methods=['DELETE'])
@login_required
def delete(alert_id):
    alert = Alert.query.filter_by(id=alert_id, user_id=current_user.id).first()
    
    if not alert:
        return jsonify({'success': False, 'error': 'Alert not found'}), 404
    
    db.session.delete(alert)
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/clear-all', methods=['POST'])
@login_required
def clear_all():
    Alert.query.filter_by(user_id=current_user.id).update({'is_read': True})
    db.session.commit()
    
    return jsonify({'success': True})

@socketio.on('connect', namespace='/alerts')
def handle_connect():
    if current_user.is_authenticated:
        join_room(f'user_{current_user.id}')
        emit('connected', {'message': 'Connected to alerts'})

@socketio.on('disconnect', namespace='/alerts')
def handle_disconnect():
    if current_user.is_authenticated:
        leave_room(f'user_{current_user.id}')

from app.utils.socketio_utils import send_alert_to_user
