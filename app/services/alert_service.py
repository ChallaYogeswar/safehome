from app.models import db, Alert
from app.utils.socketio_utils import send_alert_to_user
from flask_mail import Message
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AlertService:
    
    def create_alert(self, user_id, alert_type, title, message, severity='medium', source=None, metadata=None):
        alert = Alert(
            user_id=user_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            source=source,
            alert_metadata=metadata or {}
        )
        
        db.session.add(alert)
        db.session.commit()
        
        self._send_real_time_notification(alert)
        
        if severity in ['high', 'critical']:
            self._send_email_notification(alert)
        
        return alert
    
    def _send_real_time_notification(self, alert):
        try:
            alert_data = {
                'id': alert.id,
                'type': alert.alert_type,
                'severity': alert.severity,
                'title': alert.title,
                'message': alert.message,
                'source': alert.source,
                'created_at': alert.created_at.isoformat()
            }
            
            send_alert_to_user(alert.user_id, alert_data)
        except Exception as e:
            logger.error(f"Error sending real-time notification: {e}")
    
    def _send_email_notification(self, alert):
        try:
            from app import mail
            from app.models import User
            user = User.query.get(alert.user_id)
            
            if not user or not user.email:
                return
            
            msg = Message(
                subject=f"[SafeHome Alert] {alert.title}",
                recipients=[user.email],
                body=f"""
SafeHome Security Alert

Type: {alert.alert_type}
Severity: {alert.severity}
Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}

{alert.message}

---
This is an automated alert from SafeHome Security System.
                """.strip()
            )
            
            mail.send(msg)
            logger.info(f"Email alert sent to {user.email}")
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    def emit_event(self, event_type, user_id, payload):
        severity_map = {
            'motion_detected': 'low',
            'object_detected': 'medium',
            'face_detected': 'medium',
            'unauthorized_access': 'high',
            'multiple_failed_logins': 'critical'
        }
        
        severity = severity_map.get(event_type, 'medium')
        
        title_map = {
            'motion_detected': 'Motion Detected',
            'object_detected': 'Object Detected',
            'face_detected': 'Face Detected',
            'unauthorized_access': 'Unauthorized Access Attempt',
            'multiple_failed_logins': 'Multiple Failed Login Attempts'
        }
        
        title = title_map.get(event_type, event_type.replace('_', ' ').title())
        
        message = self._generate_message(event_type, payload)
        
        return self.create_alert(
            user_id=user_id,
            alert_type=event_type,
            title=title,
            message=message,
            severity=severity,
            source=payload.get('source'),
            metadata=payload
        )
    
    def _generate_message(self, event_type, payload):
        if event_type == 'motion_detected':
            camera = payload.get('camera_name', 'Unknown')
            return f"Motion detected on camera: {camera}"
        
        elif event_type == 'object_detected':
            camera = payload.get('camera_name', 'Unknown')
            obj_class = payload.get('object_class', 'Unknown object')
            confidence = payload.get('confidence', 0) * 100
            return f"{obj_class.title()} detected on camera {camera} (Confidence: {confidence:.1f}%)"
        
        elif event_type == 'face_detected':
            camera = payload.get('camera_name', 'Unknown')
            return f"Face detected on camera: {camera}"
        
        else:
            return f"Event: {event_type}"
