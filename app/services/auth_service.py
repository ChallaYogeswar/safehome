from app.models import db, SecurityLog
from datetime import datetime

class AuthService:
    
    def log_event(self, user_id, event_type, description, request):
        log = SecurityLog(
            user_id=user_id,
            event_type=event_type,
            event_description=description,
            ip_address=request.remote_addr if request else None,
            user_agent=request.user_agent.string if request and request.user_agent else None,
            severity=self._get_severity(event_type)
        )
        
        db.session.add(log)
        db.session.commit()
        
        return log
    
    def _get_severity(self, event_type):
        critical_events = ['account_locked', 'mfa_disabled', 'password_changed']
        warning_events = ['login_failed', 'mfa_failed']
        
        if event_type in critical_events:
            return 'critical'
        elif event_type in warning_events:
            return 'warning'
        else:
            return 'info'
    
    def check_rate_limit(self, identifier, max_attempts=5, window_minutes=15):
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        
        recent_attempts = SecurityLog.query.filter(
            SecurityLog.event_type == 'login_failed',
            SecurityLog.ip_address == identifier,
            SecurityLog.timestamp >= cutoff
        ).count()
        
        return recent_attempts < max_attempts
