ALERT_SEVERITIES = ['low', 'medium', 'high', 'critical']

ALERT_TYPES = [
    'motion_detected',
    'object_detected',
    'face_detected',
    'unauthorized_access',
    'multiple_failed_logins',
    'automation_rule',
    'notification',
    'system_alert'
]

DETECTION_TYPES = ['motion', 'object', 'face']

USER_ROLES = ['user', 'admin']

TRIGGER_TYPES = ['sensor', 'time', 'user_action', 'anomaly', 'login_event']

CONDITION_OPERATORS = ['eq', 'neq', 'gt', 'lt', 'gte', 'lte', 'contains', 'between']

ACTION_TYPES = ['send_alert', 'notify_user', 'log_event', 'control_device', 'set_mode']

SECURITY_EVENT_TYPES = [
    'user_registered',
    'login_success',
    'login_failed',
    'logout',
    'password_changed',
    'mfa_enabled',
    'mfa_disabled',
    'mfa_failed',
    'account_locked',
    'login_blocked'
]
