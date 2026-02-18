# 🛠️ SafeHome - Build & Implementation Plan

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Firebase Integration](#firebase-integration)
4. [Project Structure](#project-structure)
5. [Build Sequence](#build-sequence)
6. [Feature Implementation](#feature-implementation)
7. [Testing & Verification](#testing--verification)
8. [Deployment](#deployment)
9. [Maintenance & Updates](#maintenance--updates)

---

## 🎯 Project Overview

### Goal
Build an intelligent home access control system that:
- Monitors who enters/exits the home
- Uses facial recognition to identify people
- Automatically grants access to family members
- Requires parental approval for unknown persons
- Sends real-time notifications with photos
- Logs all entry attempts with timestamps

### Core Workflow
```
Camera Detection → Face Recognition → Decision Making → Notification + Door Control → Entry Logging
```

---

## 🏗️ Technology Stack

### Backend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | Flask 3.0 | Web application |
| **Language** | Python 3.11+ | Backend logic |
| **Face Recognition** | face_recognition + dlib | Face detection & encoding |
| **Computer Vision** | OpenCV | Image processing |
| **Database** | SQLite (local) | Local data storage |
| **Cloud Database** | Firebase Realtime DB | Cloud sync & logs |
| **Cloud Storage** | Firebase Storage | Photo storage |
| **Notifications** | Firebase Cloud Messaging | Push notifications |
| **Authentication** | Firebase Auth | User management |
| **Task Queue** | Celery + Redis | Background processing |

### Frontend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Web UI** | HTML5, CSS3, JavaScript | Dashboard interface |
| **Real-time** | Socket.IO | Live updates |
| **Camera Access** | WebRTC | Browser camera streaming |
| **Responsive** | Bootstrap 5 | Mobile-friendly |

### Hardware Integration
| Component | Options |
|-----------|---------|
| **Cameras** | Phone cameras, IP cameras, USB webcams, doorbell cams |
| **Smart Locks** | August, Yale, Schlage, Kwikset, Z-Wave compatible |
| **Communication** | WiFi, Bluetooth, Z-Wave, Zigbee |

---

## 🔥 Firebase Integration

### Services Used

#### 1. Firebase Realtime Database
**Purpose:** Store entry logs, sync across devices
```json
{
  "entries": {
    "entry_001": {
      "person_id": "john_doe",
      "person_name": "John Doe",
      "timestamp": 1707832825000,
      "camera_id": "front_door",
      "is_known": true,
      "confidence": 0.95,
      "action": "door_opened",
      "image_url": "gs://safehome/entries/entry_001.jpg",
      "approved_by": null
    }
  },
  "persons": {
    "john_doe": {
      "name": "John Doe",
      "relation": "family",
      "is_resident": true,
      "enrolled_date": 1707832800000,
      "encoding_count": 5,
      "last_seen": 1707832825000
    }
  }
}
```

#### 2. Firebase Storage
**Purpose:** Store face photos and entry images
```
/faces
  /john_doe
    - profile.jpg
    - enrollment_1.jpg
    - enrollment_2.jpg
    - enrollment_3.jpg
/entries
  - entry_001.jpg
  - entry_002.jpg
  /archive
    - 2026-02
      - entry_003.jpg
```

#### 3. Firebase Cloud Messaging (FCM)
**Purpose:** Push notifications to mobile devices
```json
{
  "to": "device_token_here",
  "notification": {
    "title": "Unknown Person at Front Door",
    "body": "Unrecognized face detected at 2:30 PM",
    "image": "https://storage.googleapis.com/safehome/entries/entry_001.jpg",
    "sound": "alert.mp3"
  },
  "data": {
    "entry_id": "entry_001",
    "camera_id": "front_door",
    "timestamp": "1707832825000",
    "action_required": "true"
  }
}
```

#### 4. Firebase Authentication
**Purpose:** User account management
```
- Email/Password authentication
- Multi-factor authentication (optional)
- User roles (admin, resident, guest)
- Session management
```

### Firebase Setup Instructions

#### Step 1: Create Firebase Project (5 minutes)
```bash
1. Go to https://console.firebase.google.com
2. Click "Add project"
3. Name: "SafeHome"
4. Enable Google Analytics: Optional
5. Create project
```

#### Step 2: Enable Required Services (10 minutes)
```bash
# Realtime Database
1. Build → Realtime Database → Create Database
2. Choose location: us-central1 (or nearest)
3. Security rules: Start in test mode (secure later)

# Storage
1. Build → Storage → Get Started
2. Security rules: Start in test mode (secure later)

# Cloud Messaging
1. Build → Cloud Messaging → Get Started
2. No additional setup needed

# Authentication
1. Build → Authentication → Get Started
2. Sign-in method → Email/Password → Enable
```

#### Step 3: Generate Service Account Key (2 minutes)
```bash
1. Project Settings (gear icon)
2. Service Accounts tab
3. Generate New Private Key
4. Download JSON → Save as "firebase-credentials.json"
5. Keep this file SECRET (add to .gitignore)
```

#### Step 4: Configure Firebase in Project (3 minutes)
```bash
# Install Firebase Admin SDK
pip install firebase-admin

# Add to .env file
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
FIREBASE_DATABASE_URL=https://safehome-xxxxx.firebaseio.com
FIREBASE_STORAGE_BUCKET=safehome-xxxxx.appspot.com
FIREBASE_PROJECT_ID=safehome-xxxxx
```

#### Step 5: Initialize Firebase in Code
```python
# app/__init__.py
import firebase_admin
from firebase_admin import credentials, db, storage, messaging

def init_firebase(app):
    """Initialize Firebase Admin SDK"""
    cred = credentials.Certificate(
        app.config['FIREBASE_CREDENTIALS_PATH']
    )
    firebase_admin.initialize_app(cred, {
        'databaseURL': app.config['FIREBASE_DATABASE_URL'],
        'storageBucket': app.config['FIREBASE_STORAGE_BUCKET']
    })
    app.logger.info("Firebase initialized successfully")
```

---

## 📁 Project Structure

```
SafeHome/
├── app/
│   ├── __init__.py                 # App factory + Firebase init
│   ├── models.py                   # SQLAlchemy models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py                # User authentication
│   │   ├── dashboard.py           # Main dashboard
│   │   ├── camera.py              # Camera management
│   │   ├── face.py                # Face enrollment & recognition
│   │   ├── entries.py             # Entry logs
│   │   └── notifications.py       # Notification management
│   ├── services/
│   │   ├── __init__.py
│   │   ├── face_recognition_service.py    # Face detection & matching
│   │   ├── firebase_service.py            # Firebase operations
│   │   ├── notification_service.py        # Push notifications
│   │   ├── camera_service.py              # Camera stream handling
│   │   ├── door_control_service.py        # Smart lock integration
│   │   └── entry_logger.py                # Entry logging
│   ├── utils/
│   │   ├── decorators.py          # Auth decorators
│   │   ├── validators.py          # Input validation
│   │   └── constants.py           # Configuration constants
│   ├── static/
│   │   ├── css/
│   │   │   ├── main.css
│   │   │   └── mobile.css
│   │   ├── js/
│   │   │   ├── app.js
│   │   │   ├── camera.js
│   │   │   ├── face-enrollment.js
│   │   │   ├── notifications.js
│   │   │   └── firebase-client.js
│   │   └── images/
│   └── templates/
│       ├── base.html
│       ├── dashboard.html
│       ├── camera.html
│       ├── people.html
│       ├── entries.html
│       └── auth/
│           ├── login.html
│           └── register.html
├── firebase-credentials.json       # Firebase service account (SECRET)
├── ml_models/                      # Face recognition models
│   └── shape_predictor_68_face_landmarks.dat
├── uploads/                        # Temporary storage
│   ├── faces/
│   └── entries/
├── logs/
├── tests/
├── migrations/
├── config.py
├── SafeHome.py
├── requirements.txt
├── .env
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🔨 Build Sequence

### Phase 1: Environment Setup (30 minutes)

#### 1.1 Create Project Directory
```bash
mkdir SafeHome
cd SafeHome
```

#### 1.2 Initialize Virtual Environment
```bash
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows
```

#### 1.3 Create requirements.txt
```bash
cat > requirements.txt << 'EOF'
# Core Framework
Flask==3.0.0
flask-sqlalchemy==3.1.1
flask-migrate==4.0.5
flask-login==0.6.3
flask-socketio==5.3.5
flask-cors==4.0.0

# Face Recognition
face-recognition==1.3.0
opencv-python==4.9.0.80
dlib==19.24.2
Pillow==10.2.0
numpy==1.26.3

# Firebase
firebase-admin==6.4.0

# Background Tasks
celery==5.3.4
redis==5.0.1

# Security
bcrypt==4.1.2
python-jose[cryptography]==3.3.0
python-dotenv==1.0.0

# Utilities
requests==2.31.0
python-dateutil==2.8.2
pytz==2023.3

# WebRTC/Streaming
eventlet==0.33.3
gevent==23.9.1

# Production Server
gunicorn==21.2.0
EOF
```

#### 1.4 Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt

# Install dlib (may take 10-15 minutes)
# If dlib fails, see troubleshooting section
```

#### 1.5 Download Face Recognition Models
```bash
mkdir -p ml_models
cd ml_models

# Download shape predictor (68-point facial landmarks)
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bunzip2 shape_predictor_68_face_landmarks.dat.bz2

cd ..
```

---

### Phase 2: Firebase Configuration (20 minutes)

#### 2.1 Create Firebase Project (see Firebase Setup above)

#### 2.2 Create .env File
```bash
cat > .env << 'EOF'
# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
FLASK_ENV=development
FLASK_APP=SafeHome.py

# Database
DATABASE_URL=sqlite:///safehome.db

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
FIREBASE_DATABASE_URL=https://safehome-xxxxx.firebaseio.com
FIREBASE_STORAGE_BUCKET=safehome-xxxxx.appspot.com
FIREBASE_PROJECT_ID=safehome-xxxxx

# Face Recognition Settings
FACE_RECOGNITION_TOLERANCE=0.6
MIN_FACE_ENCODINGS=2
MAX_FACES_PER_FRAME=5

# Notification Settings
ENABLE_PUSH_NOTIFICATIONS=true
ENABLE_EMAIL_NOTIFICATIONS=true
NOTIFICATION_QUIET_HOURS=22:00-07:00

# Door Control
AUTO_OPEN_RESIDENTS=true
AUTO_OPEN_DURATION=5
REQUIRE_APPROVAL_FOR_GUESTS=true

# Celery/Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security
SESSION_TIMEOUT=3600
MAX_LOGIN_ATTEMPTS=5
JWT_SECRET_KEY=another-secret-key-change-this
EOF
```

#### 2.3 Place Firebase Credentials
```bash
# Download firebase-credentials.json from Firebase Console
# Place it in project root
mv ~/Downloads/safehome-xxxxx-firebase-adminsdk-xxxxx.json firebase-credentials.json

# Add to .gitignore
echo "firebase-credentials.json" >> .gitignore
```

---

### Phase 3: Core Application (2-3 hours)

#### 3.1 Create config.py
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///safehome.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH')
    FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL')
    FIREBASE_STORAGE_BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET')
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
    
    # Face Recognition
    FACE_RECOGNITION_TOLERANCE = float(os.getenv('FACE_RECOGNITION_TOLERANCE', 0.6))
    MIN_FACE_ENCODINGS = int(os.getenv('MIN_FACE_ENCODINGS', 2))
    MAX_FACES_PER_FRAME = int(os.getenv('MAX_FACES_PER_FRAME', 5))
    
    # Uploads
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    
    # Session
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 3600))
    
    # Celery
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
```

#### 3.2 Create Database Models (app/models.py)
```python
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User accounts (parents/guardians)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='admin')  # admin, user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Firebase device tokens for push notifications
    device_tokens = db.relationship('DeviceToken', backref='user', lazy=True)

class DeviceToken(db.Model):
    """Firebase device tokens for push notifications"""
    __tablename__ = 'device_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    device_type = db.Column(db.String(20))  # ios, android, web
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Camera(db.Model):
    """Camera/Entry point configuration"""
    __tablename__ = 'cameras'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # "Front Door"
    location = db.Column(db.String(100))  # "Main Entrance"
    camera_type = db.Column(db.String(20))  # mobile, ip, usb
    stream_url = db.Column(db.String(255))  # RTSP URL for IP cameras
    is_active = db.Column(db.Boolean, default=True)
    face_detection_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FacePerson(db.Model):
    """Enrolled persons (family, guests)"""
    __tablename__ = 'face_persons'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    relation = db.Column(db.String(50))  # family, guest, staff
    is_resident = db.Column(db.Boolean, default=True)  # Can open doors?
    profile_image = db.Column(db.String(255))
    firebase_id = db.Column(db.String(100))  # Firebase Realtime DB ID
    enrolled_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Face encodings stored locally
    encodings = db.relationship('FaceEncoding', backref='person', lazy=True, cascade='all, delete-orphan')

class FaceEncoding(db.Model):
    """Face encodings (128-dimensional vectors)"""
    __tablename__ = 'face_encodings'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('face_persons.id'), nullable=False)
    encoding_data = db.Column(db.Text, nullable=False)  # JSON array of 128 floats
    image_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_encoding(self):
        """Convert stored JSON back to numpy array"""
        return json.loads(self.encoding_data)
    
    def set_encoding(self, encoding_array):
        """Store numpy array as JSON"""
        self.encoding_data = json.dumps(encoding_array.tolist())

class EntryLog(db.Model):
    """Local entry log (synced with Firebase)"""
    __tablename__ = 'entry_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    firebase_id = db.Column(db.String(100))  # Firebase entry ID
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'))
    person_id = db.Column(db.Integer, db.ForeignKey('face_persons.id'), nullable=True)
    person_name = db.Column(db.String(100))
    is_known = db.Column(db.Boolean, default=False)
    confidence = db.Column(db.Float)
    image_path = db.Column(db.String(255))  # Local path
    firebase_image_url = db.Column(db.String(500))  # Firebase Storage URL
    action = db.Column(db.String(50))  # door_opened, entry_denied, pending_approval
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
```

#### 3.3 Create App Factory (app/__init__.py)
```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
import firebase_admin
from firebase_admin import credentials
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Initialize Firebase
    if not firebase_admin._apps:
        cred = credentials.Certificate(app.config['FIREBASE_CREDENTIALS_PATH'])
        firebase_admin.initialize_app(cred, {
            'databaseURL': app.config['FIREBASE_DATABASE_URL'],
            'storageBucket': app.config['FIREBASE_STORAGE_BUCKET']
        })
        app.logger.info("✅ Firebase initialized")
    
    # Register blueprints
    from app.routes import auth, dashboard, camera, face, entries, notifications
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(camera.bp)
    app.register_blueprint(face.bp)
    app.register_blueprint(entries.bp)
    app.register_blueprint(notifications.bp)
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    return app
```

---

### Phase 4: Face Recognition Service (1-2 hours)

#### 4.1 Create Face Recognition Service (app/services/face_recognition_service.py)
```python
import face_recognition
import numpy as np
from app.models import FacePerson, FaceEncoding, db
from flask import current_app

class FaceRecognitionService:
    """Handle face detection, encoding, and recognition"""
    
    def __init__(self):
        self.tolerance = current_app.config['FACE_RECOGNITION_TOLERANCE']
    
    def enroll_person(self, name, relation, is_resident, image_files):
        """
        Enroll a new person with multiple photos
        
        Args:
            name: Person's name
            relation: 'family', 'guest', 'staff'
            is_resident: Boolean - can they open doors?
            image_files: List of image file objects
        
        Returns:
            (person_object, encoding_count) or (None, error_message)
        """
        encodings = []
        
        for image_file in image_files:
            # Load image
            image = face_recognition.load_image_file(image_file)
            
            # Detect faces
            face_locations = face_recognition.face_locations(image)
            
            if len(face_locations) == 0:
                continue  # Skip images with no faces
            
            if len(face_locations) > 1:
                continue  # Skip images with multiple faces
            
            # Extract encoding (128-dimensional vector)
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if len(face_encodings) > 0:
                encodings.append(face_encodings[0])
        
        # Validate minimum encodings
        min_encodings = current_app.config['MIN_FACE_ENCODINGS']
        if len(encodings) < min_encodings:
            return None, f"Need at least {min_encodings} clear photos. Got {len(encodings)}."
        
        # Create person record
        person = FacePerson(
            name=name,
            relation=relation,
            is_resident=is_resident
        )
        db.session.add(person)
        db.session.flush()  # Get person.id
        
        # Store encodings
        for idx, encoding in enumerate(encodings):
            face_enc = FaceEncoding(
                person_id=person.id
            )
            face_enc.set_encoding(encoding)
            db.session.add(face_enc)
        
        db.session.commit()
        
        return person, len(encodings)
    
    def recognize_face(self, image_file):
        """
        Recognize a face from an image
        
        Args:
            image_file: Image file object or path
        
        Returns:
            {
                'is_known': bool,
                'person_id': int or None,
                'person_name': str or None,
                'confidence': float (0-1),
                'relation': str or None,
                'is_resident': bool
            }
        """
        # Load image
        if isinstance(image_file, str):
            image = face_recognition.load_image_file(image_file)
        else:
            image = face_recognition.load_image_file(image_file)
        
        # Detect faces
        face_locations = face_recognition.face_locations(image)
        
        if len(face_locations) == 0:
            return {
                'is_known': False,
                'person_id': None,
                'person_name': 'No face detected',
                'confidence': 0.0,
                'relation': None,
                'is_resident': False
            }
        
        # Get encoding of first face
        face_encodings = face_recognition.face_encodings(image, face_locations)
        unknown_encoding = face_encodings[0]
        
        # Get all enrolled persons
        persons = FacePerson.query.all()
        
        best_match = None
        best_distance = float('inf')
        
        for person in persons:
            for face_enc in person.encodings:
                known_encoding = np.array(face_enc.get_encoding())
                
                # Calculate distance
                distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
                
                if distance < best_distance:
                    best_distance = distance
                    best_match = person
        
        # Check if match is good enough
        if best_distance < self.tolerance:
            confidence = 1.0 - best_distance
            return {
                'is_known': True,
                'person_id': best_match.id,
                'person_name': best_match.name,
                'confidence': confidence,
                'relation': best_match.relation,
                'is_resident': best_match.is_resident
            }
        else:
            return {
                'is_known': False,
                'person_id': None,
                'person_name': 'Unknown Person',
                'confidence': 0.0,
                'relation': None,
                'is_resident': False
            }
```

---

### Phase 5: Firebase Service (1 hour)

#### 5.1 Create Firebase Service (app/services/firebase_service.py)
```python
from firebase_admin import db as firebase_db, storage, messaging
from datetime import datetime
import uuid

class FirebaseService:
    """Handle all Firebase operations"""
    
    def __init__(self):
        self.db_ref = firebase_db.reference()
        self.bucket = storage.bucket()
    
    def log_entry(self, entry_data):
        """
        Log entry to Firebase Realtime Database
        
        Args:
            entry_data: {
                'person_id': str or None,
                'person_name': str,
                'camera_id': str,
                'is_known': bool,
                'confidence': float,
                'action': str,
                'timestamp': int (epoch ms),
                'image_url': str,
                'approved_by': str or None
            }
        
        Returns:
            firebase_entry_id: str
        """
        entry_id = f"entry_{uuid.uuid4().hex[:12]}"
        
        self.db_ref.child('entries').child(entry_id).set({
            'person_id': entry_data.get('person_id'),
            'person_name': entry_data.get('person_name'),
            'camera_id': entry_data.get('camera_id'),
            'is_known': entry_data.get('is_known', False),
            'confidence': entry_data.get('confidence', 0.0),
            'action': entry_data.get('action', 'pending'),
            'timestamp': entry_data.get('timestamp', int(datetime.utcnow().timestamp() * 1000)),
            'image_url': entry_data.get('image_url'),
            'approved_by': entry_data.get('approved_by')
        })
        
        return entry_id
    
    def upload_image(self, image_path, destination_path):
        """
        Upload image to Firebase Storage
        
        Args:
            image_path: Local file path
            destination_path: Path in Firebase Storage (e.g., 'entries/entry_001.jpg')
        
        Returns:
            public_url: str
        """
        blob = self.bucket.blob(destination_path)
        blob.upload_from_filename(image_path)
        blob.make_public()
        
        return blob.public_url
    
    def send_push_notification(self, device_tokens, notification_data):
        """
        Send push notification via FCM
        
        Args:
            device_tokens: List of device tokens
            notification_data: {
                'title': str,
                'body': str,
                'image_url': str,
                'data': dict (custom data)
            }
        
        Returns:
            response: FCM response object
        """
        message = messaging.MulticastMessage(
            tokens=device_tokens,
            notification=messaging.Notification(
                title=notification_data['title'],
                body=notification_data['body'],
                image=notification_data.get('image_url')
            ),
            data=notification_data.get('data', {}),
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound='alert',
                    channel_id='safehome_alerts'
                )
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='alert.wav',
                        badge=1
                    )
                )
            )
        )
        
        response = messaging.send_multicast(message)
        return response
    
    def sync_person(self, person_data):
        """
        Sync enrolled person to Firebase
        
        Args:
            person_data: {
                'id': str,
                'name': str,
                'relation': str,
                'is_resident': bool,
                'enrolled_date': int,
                'encoding_count': int
            }
        
        Returns:
            firebase_person_id: str
        """
        person_id = person_data['id']
        
        self.db_ref.child('persons').child(person_id).set({
            'name': person_data['name'],
            'relation': person_data['relation'],
            'is_resident': person_data['is_resident'],
            'enrolled_date': person_data['enrolled_date'],
            'encoding_count': person_data['encoding_count'],
            'last_seen': None
        })
        
        return person_id
```

---

### Phase 6: Routes & API (2-3 hours)

#### 6.1 Face Enrollment Route (app/routes/face.py)
```python
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.services.face_recognition_service import FaceRecognitionService
from app.services.firebase_service import FirebaseService
from app.models import db
from werkzeug.utils import secure_filename
import os
from datetime import datetime

bp = Blueprint('face', __name__, url_prefix='/face')

@bp.route('/enroll', methods=['POST'])
@login_required
def enroll_person():
    """Enroll a new person with face photos"""
    
    # Get form data
    name = request.form.get('person_name')
    relation = request.form.get('relation', 'family')
    is_resident = request.form.get('is_resident', 'true').lower() == 'true'
    
    # Get uploaded images
    images = request.files.getlist('images')
    
    if not name or not images:
        return jsonify({'success': False, 'error': 'Name and images required'}), 400
    
    if len(images) < current_app.config['MIN_FACE_ENCODINGS']:
        return jsonify({
            'success': False,
            'error': f'Minimum {current_app.config["MIN_FACE_ENCODINGS"]} photos required'
        }), 400
    
    # Save images temporarily
    temp_paths = []
    for img in images:
        filename = secure_filename(img.filename)
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'faces', filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        img.save(path)
        temp_paths.append(path)
    
    # Enroll person
    face_service = FaceRecognitionService()
    person, result = face_service.enroll_person(name, relation, is_resident, temp_paths)
    
    if person is None:
        # Enrollment failed
        return jsonify({'success': False, 'error': result}), 400
    
    # Sync to Firebase
    firebase_service = FirebaseService()
    firebase_id = firebase_service.sync_person({
        'id': str(person.id),
        'name': person.name,
        'relation': person.relation,
        'is_resident': person.is_resident,
        'enrolled_date': int(person.enrolled_date.timestamp() * 1000),
        'encoding_count': result
    })
    
    person.firebase_id = firebase_id
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Successfully enrolled {name} with {result} face encodings',
        'person_id': person.id,
        'encoding_count': result
    })

@bp.route('/recognize', methods=['POST'])
@login_required
def recognize_face():
    """Recognize a face from uploaded image"""
    
    camera_id = request.form.get('camera_id')
    image = request.files.get('image')
    
    if not camera_id or not image:
        return jsonify({'success': False, 'error': 'Camera ID and image required'}), 400
    
    # Save image temporarily
    filename = secure_filename(f"{datetime.utcnow().timestamp()}.jpg")
    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'entries', filename)
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    image.save(image_path)
    
    # Recognize face
    face_service = FaceRecognitionService()
    recognition = face_service.recognize_face(image_path)
    
    # Upload to Firebase Storage
    firebase_service = FirebaseService()
    firebase_image_url = firebase_service.upload_image(
        image_path,
        f'entries/{filename}'
    )
    
    # Log entry
    entry_data = {
        'person_id': str(recognition['person_id']) if recognition['person_id'] else None,
        'person_name': recognition['person_name'],
        'camera_id': camera_id,
        'is_known': recognition['is_known'],
        'confidence': recognition['confidence'],
        'action': 'door_opened' if (recognition['is_known'] and recognition['is_resident']) else 'entry_denied',
        'timestamp': int(datetime.utcnow().timestamp() * 1000),
        'image_url': firebase_image_url
    }
    
    firebase_entry_id = firebase_service.log_entry(entry_data)
    
    # Send notification if unknown or guest
    if not recognition['is_known'] or (recognition['is_known'] and not recognition['is_resident']):
        notification_service = NotificationService()
        notification_service.send_entry_alert(entry_data)
    
    return jsonify({
        'success': True,
        'recognition': recognition,
        'entry_id': firebase_entry_id,
        'image_url': firebase_image_url
    })
```

---

### Phase 7: Notification Service (1 hour)

#### 7.1 Create Notification Service (app/services/notification_service.py)
```python
from app.services.firebase_service import FirebaseService
from app.models import User, DeviceToken
from datetime import datetime

class NotificationService:
    """Handle push notifications and alerts"""
    
    def __init__(self):
        self.firebase = FirebaseService()
    
    def send_entry_alert(self, entry_data):
        """
        Send alert for entry attempt
        
        Args:
            entry_data: Entry information dict
        """
        # Get all admin device tokens
        admin_users = User.query.filter_by(role='admin').all()
        tokens = []
        
        for user in admin_users:
            for device_token in user.device_tokens:
                tokens.append(device_token.token)
        
        if not tokens:
            return  # No devices to notify
        
        # Prepare notification
        is_known = entry_data.get('is_known', False)
        person_name = entry_data.get('person_name', 'Unknown Person')
        camera_id = entry_data.get('camera_id', 'Door')
        
        if is_known:
            title = f"{person_name} at {camera_id}"
            body = f"Entry detected at {datetime.now().strftime('%I:%M %p')}"
        else:
            title = f"🚨 Unknown Person at {camera_id}"
            body = f"Unrecognized face detected - Approval Required"
        
        notification_data = {
            'title': title,
            'body': body,
            'image_url': entry_data.get('image_url'),
            'data': {
                'entry_id': entry_data.get('entry_id', ''),
                'camera_id': camera_id,
                'person_name': person_name,
                'is_known': str(is_known),
                'timestamp': str(entry_data.get('timestamp', '')),
                'action_required': str(not is_known)
            }
        }
        
        # Send notification
        response = self.firebase.send_push_notification(tokens, notification_data)
        
        return response
```

---

### Phase 8: Frontend (2-3 hours)

#### 8.1 Create Dashboard Template (app/templates/dashboard.html)
```html
{% extends "base.html" %}

{% block content %}
<div class="container mt-4">
    <h2>SafeHome Dashboard</h2>
    
    <!-- Stats Cards -->
    <div class="row mt-4">
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Today's Entries</h5>
                    <h2 id="today-entries">0</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Enrolled People</h5>
                    <h2 id="enrolled-count">0</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Active Cameras</h5>
                    <h2 id="active-cameras">0</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Unknown Attempts</h5>
                    <h2 id="unknown-attempts">0</h2>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Recent Entries -->
    <div class="row mt-4">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <h5>Recent Activity</h5>
                </div>
                <div class="card-body">
                    <div id="recent-entries">
                        <!-- Populated by JavaScript -->
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script src="{{ url_for('static', filename='js/dashboard.js') }}"></script>
{% endblock %}
```

#### 8.2 Create Dashboard JavaScript (app/static/js/dashboard.js)
```javascript
// Initialize Firebase (client-side)
const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "safehome-xxxxx.firebaseapp.com",
    databaseURL: "https://safehome-xxxxx.firebaseio.com",
    projectId: "safehome-xxxxx",
    storageBucket: "safehome-xxxxx.appspot.com",
    messagingSenderId: "YOUR_SENDER_ID",
    appId: "YOUR_APP_ID"
};

firebase.initializeApp(firebaseConfig);
const database = firebase.database();

// Listen for new entries
database.ref('entries').on('child_added', (snapshot) => {
    const entry = snapshot.val();
    addEntryToList(entry);
    updateStats();
});

function addEntryToList(entry) {
    const entryHtml = `
        <div class="entry-item mb-3 p-3 border rounded">
            <div class="row">
                <div class="col-md-2">
                    <img src="${entry.image_url}" class="img-fluid rounded" alt="Entry photo">
                </div>
                <div class="col-md-10">
                    <h5>${entry.person_name}</h5>
                    <p class="mb-1">
                        <strong>Time:</strong> ${new Date(entry.timestamp).toLocaleString()}<br>
                        <strong>Location:</strong> ${entry.camera_id}<br>
                        <strong>Status:</strong> 
                        <span class="badge ${entry.is_known ? 'bg-success' : 'bg-danger'}">
                            ${entry.is_known ? 'Known' : 'Unknown'}
                        </span>
                    </p>
                    ${!entry.is_known ? `
                        <button class="btn btn-sm btn-success" onclick="approveEntry('${snapshot.key}')">
                            Approve Entry
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="denyEntry('${snapshot.key}')">
                            Deny Entry
                        </button>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('recent-entries').insertAdjacentHTML('afterbegin', entryHtml);
}

function updateStats() {
    // Update statistics
    database.ref('entries').once('value', (snapshot) => {
        const entries = snapshot.val() || {};
        const today = new Date().toDateString();
        
        let todayCount = 0;
        let unknownCount = 0;
        
        Object.values(entries).forEach(entry => {
            const entryDate = new Date(entry.timestamp).toDateString();
            if (entryDate === today) {
                todayCount++;
                if (!entry.is_known) unknownCount++;
            }
        });
        
        document.getElementById('today-entries').textContent = todayCount;
        document.getElementById('unknown-attempts').textContent = unknownCount;
    });
}

function approveEntry(entryId) {
    // Send approval to backend
    fetch(`/entries/approve/${entryId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Entry approved! Door opened.');
            location.reload();
        }
    });
}

function denyEntry(entryId) {
    // Send denial to backend
    fetch(`/entries/deny/${entryId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Entry denied.');
            location.reload();
        }
    });
}

// Load initial data
updateStats();
