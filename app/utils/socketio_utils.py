def send_alert_to_user(user_id, alert_data):
    """Send real-time alert notification to user via WebSocket"""
    try:
        # Import here to avoid circular imports
        from app import socketio

        alert_data_formatted = {
            'id': alert_data.get('id'),
            'type': alert_data.get('alert_type') or alert_data.get('type'),
            'severity': alert_data.get('severity'),
            'title': alert_data.get('title'),
            'message': alert_data.get('message'),
            'source': alert_data.get('source'),
            'created_at': alert_data.get('created_at')
        }

        socketio.emit('new_alert', alert_data_formatted,
                     room=f'user_{user_id}',
                     namespace='/alerts')
    except Exception as e:
        print(f"Error sending real-time notification: {e}")