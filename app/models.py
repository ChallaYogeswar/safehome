from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp

db = SQLAlchemy()

def utc_now():
    """Return current UTC time in timezone-aware format"""
    return datetime.now(timezone.utc)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.String(32))
    
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    cameras = db.relationship('Camera', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    rules = db.relationship('AutomationRule', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    device_tokens = db.relationship('DeviceToken', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_mfa_secret(self):
        self.mfa_secret = pyotp.random_base32()
        return self.mfa_secret
    
    def verify_mfa_token(self, token):
        if not self.mfa_enabled or not self.mfa_secret:
            return False
        totp = pyotp.TOTP(self.mfa_secret)
        return totp.verify(token, valid_window=1)

class DeviceToken(db.Model):
    """Firebase device tokens for push notifications"""
    __tablename__ = 'device_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    device_type = db.Column(db.String(20))  # ios, android, web
    device_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    last_used = db.Column(db.DateTime)

class Camera(db.Model):
    __tablename__ = 'cameras'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    
    stream_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    is_recording = db.Column(db.Boolean, default=False)
    
    motion_enabled = db.Column(db.Boolean, default=True)
    object_detection_enabled = db.Column(db.Boolean, default=True)
    face_detection_enabled = db.Column(db.Boolean, default=False)
    access_control_enabled = db.Column(db.Boolean, default=False)
    
    last_motion = db.Column(db.DateTime)
    last_detection = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    detections = db.relationship('Detection', backref='camera', lazy='dynamic', cascade='all, delete-orphan')
    access_logs = db.relationship('AccessLog', backref='camera', lazy='dynamic', cascade='all, delete-orphan')

class Detection(db.Model):
    __tablename__ = 'detections'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False, index=True)
    
    detection_type = db.Column(db.String(50), nullable=False, index=True)
    object_class = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    
    bbox_x = db.Column(db.Integer)
    bbox_y = db.Column(db.Integer)
    bbox_width = db.Column(db.Integer)
    bbox_height = db.Column(db.Integer)
    
    image_path = db.Column(db.String(500))
    detection_metadata = db.Column(db.JSON)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    alert_type = db.Column(db.String(50), nullable=False, index=True)
    severity = db.Column(db.String(20), default='medium', index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    source = db.Column(db.String(100))
    alert_metadata = db.Column(db.JSON)
    
    is_read = db.Column(db.Boolean, default=False, index=True)
    is_acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

class AutomationRule(db.Model):
    __tablename__ = 'automation_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    trigger_type = db.Column(db.String(50), nullable=False)
    trigger_config = db.Column(db.JSON, nullable=False)
    
    conditions = db.Column(db.JSON)
    actions = db.Column(db.JSON, nullable=False)
    
    cron_expression = db.Column(db.String(100))
    
    last_triggered = db.Column(db.DateTime)
    trigger_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SecurityLog(db.Model):
    __tablename__ = 'security_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    
    event_type = db.Column(db.String(50), nullable=False, index=True)
    event_description = db.Column(db.Text, nullable=False)
    
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    
    severity = db.Column(db.String(20), default='info')
    log_metadata = db.Column(db.JSON)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

class MLModel(db.Model):
    __tablename__ = 'ml_models'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    model_type = db.Column(db.String(50), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    
    file_path = db.Column(db.String(500), nullable=False)
    accuracy = db.Column(db.Float)
    
    is_active = db.Column(db.Boolean, default=False)
    
    training_data_size = db.Column(db.Integer)
    training_date = db.Column(db.DateTime)
    
    model_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=utc_now)

class FacePerson(db.Model):
    """Known person enrolled for face recognition"""
    __tablename__ = 'face_persons'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    name = db.Column(db.String(100), nullable=False)
    relation = db.Column(db.String(50))  # e.g., 'family', 'guest', 'staff'
    is_resident = db.Column(db.Boolean, default=True)  # Can they access/open doors?
    
    profile_image = db.Column(db.String(500))  # Path to main profile photo
    firebase_id = db.Column(db.String(100))  # Firebase Realtime DB sync ID
    face_encodings = db.relationship('FaceEncoding', backref='person', lazy='dynamic', cascade='all, delete-orphan')
    
    recognition_count = db.Column(db.Integer, default=0)
    last_recognized = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

class FaceEncoding(db.Model):
    """Stores face encodings (128-dim vectors) for recognition"""
    __tablename__ = 'face_encodings'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('face_persons.id'), nullable=False, index=True)
    
    encoding = db.Column(db.JSON, nullable=False)  # Store 128-dim vector as JSON array
    image_path = db.Column(db.String(500))
    
    created_at = db.Column(db.DateTime, default=utc_now)

class AccessLog(db.Model):
    """Log of access attempts (recognized/unknown persons)"""
    __tablename__ = 'access_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False, index=True)
    person_id = db.Column(db.Integer, db.ForeignKey('face_persons.id'), index=True)  # None if unknown
    
    person_name = db.Column(db.String(100))  # Original detected/confirmed name
    is_known = db.Column(db.Boolean, default=False)
    confidence = db.Column(db.Float)
    
    image_path = db.Column(db.String(500))
    firebase_id = db.Column(db.String(100))  # Firebase entry ID for sync
    firebase_image_url = db.Column(db.String(500))  # Firebase Storage public URL
    access_granted = db.Column(db.Boolean, default=False)
    action = db.Column(db.String(50))  # 'door_opened', 'door_denied', 'alert_sent', 'pending_approval'
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    timestamp = db.Column(db.DateTime, default=utc_now, index=True)
