"""
Notification Service
Handles push notifications and alerts via Firebase Cloud Messaging
"""

from flask import current_app
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Handle push notifications and entry alerts"""
    
    def __init__(self):
        from app.services.firebase_service import FirebaseService
        self.firebase = FirebaseService()
    
    def send_entry_alert(self, entry_data):
        """
        Send alert notification for an entry attempt
        
        Args:
            entry_data: {
                'person_name': str,
                'camera_id': str,
                'is_known': bool,
                'confidence': float,
                'image_url': str,
                'entry_id': str,
                'timestamp': int
            }
        
        Returns:
            FCM response or None
        """
        if not current_app.config.get('ENABLE_PUSH_NOTIFICATIONS', True):
            logger.info("Push notifications disabled — skipping entry alert")
            return None
        
        # Check quiet hours
        if self._is_quiet_hours():
            logger.info("Quiet hours active — suppressing non-critical notification")
            # Still send for unknown persons during quiet hours
            if entry_data.get('is_known', False):
                return None
        
        # Get all admin device tokens
        tokens = self._get_admin_tokens()
        
        if not tokens:
            logger.warning("No device tokens found — cannot send notification")
            return None
        
        # Prepare notification content
        is_known = entry_data.get('is_known', False)
        person_name = entry_data.get('person_name', 'Unknown Person')
        camera_id = entry_data.get('camera_id', 'Door')
        timestamp = entry_data.get('timestamp')
        
        if timestamp:
            time_str = datetime.fromtimestamp(timestamp / 1000).strftime('%I:%M %p')
        else:
            time_str = datetime.now().strftime('%I:%M %p')
        
        if is_known:
            title = f"👤 {person_name} at {camera_id}"
            body = f"Known person detected at {time_str}"
        else:
            title = f"🚨 Unknown Person at {camera_id}"
            body = f"Unrecognized face detected at {time_str} — Approval Required"
        
        notification_data = {
            'title': title,
            'body': body,
            'image_url': entry_data.get('image_url'),
            'data': {
                'entry_id': entry_data.get('entry_id', ''),
                'camera_id': str(camera_id),
                'person_name': person_name,
                'is_known': str(is_known),
                'timestamp': str(entry_data.get('timestamp', '')),
                'action_required': str(not is_known),
                'type': 'entry_alert'
            }
        }
        
        # Send notification
        response = self.firebase.send_push_notification(tokens, notification_data)
        return response
    
    def send_door_action_notification(self, action, person_name, camera_id, approved_by=None):
        """
        Send notification about a door action (opened/denied)
        
        Args:
            action: 'door_opened' or 'entry_denied'
            person_name: Name of the person
            camera_id: Camera/location identifier
            approved_by: Username who approved (if applicable)
        """
        tokens = self._get_admin_tokens()
        if not tokens:
            return None
        
        if action == 'door_opened':
            title = f"🔓 Door Opened for {person_name}"
            body = f"Access granted at {camera_id}"
            if approved_by:
                body += f" (approved by {approved_by})"
        else:
            title = f"🔒 Entry Denied for {person_name}"
            body = f"Access denied at {camera_id}"
            if approved_by:
                body += f" (denied by {approved_by})"
        
        notification_data = {
            'title': title,
            'body': body,
            'data': {
                'type': 'door_action',
                'action': action,
                'person_name': person_name,
                'camera_id': str(camera_id)
            }
        }
        
        return self.firebase.send_push_notification(tokens, notification_data)
    
    def send_system_notification(self, title, body, data=None):
        """
        Send a general system notification to all admins
        
        Args:
            title: Notification title
            body: Notification body text
            data: Optional custom data dict
        """
        tokens = self._get_admin_tokens()
        if not tokens:
            return None
        
        notification_data = {
            'title': title,
            'body': body,
            'data': {**(data or {}), 'type': 'system'}
        }
        
        return self.firebase.send_push_notification(tokens, notification_data)
    
    def _get_admin_tokens(self):
        """Get all active device tokens for admin users"""
        from app.models import User, DeviceToken
        
        try:
            admin_users = User.query.filter_by(role='admin').all()
            tokens = []
            
            for user in admin_users:
                active_tokens = DeviceToken.query.filter_by(
                    user_id=user.id,
                    is_active=True
                ).all()
                tokens.extend([dt.token for dt in active_tokens])
            
            return tokens
        except Exception as e:
            logger.error(f"Error fetching admin tokens: {e}")
            return []
    
    def _is_quiet_hours(self):
        """Check if current time is within quiet hours"""
        try:
            quiet_hours = current_app.config.get('NOTIFICATION_QUIET_HOURS', '22:00-07:00')
            if not quiet_hours or '-' not in quiet_hours:
                return False
            
            start_str, end_str = quiet_hours.split('-')
            start_h, start_m = map(int, start_str.strip().split(':'))
            end_h, end_m = map(int, end_str.strip().split(':'))
            
            now = datetime.now()
            current_minutes = now.hour * 60 + now.minute
            start_minutes = start_h * 60 + start_m
            end_minutes = end_h * 60 + end_m
            
            if start_minutes > end_minutes:
                # Overnight quiet hours (e.g., 22:00 - 07:00)
                return current_minutes >= start_minutes or current_minutes < end_minutes
            else:
                return start_minutes <= current_minutes < end_minutes
                
        except Exception as e:
            logger.error(f"Error checking quiet hours: {e}")
            return False
