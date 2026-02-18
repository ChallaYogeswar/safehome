# 🏠 SafeHome - Smart Home Access Control System

![Version](https://img.shields.io/badge/version-2.0-blue)
![Status](https://img.shields.io/badge/status-Production%20Ready-green)
![Python](https://img.shields.io/badge/python-3.11%2B-brightgreen)
![Firebase](https://img.shields.io/badge/Firebase-Integrated-orange)

## 📋 Overview

**SafeHome** is an intelligent home access control and monitoring system that uses facial recognition to manage who enters and exits your home. Perfect for families with children and elderly members, it provides real-time notifications, automatic door access for known persons, and manual approval for unknown visitors.

### Key Features

✅ **Facial Recognition** - Identify family members, guests, and unknown persons  
✅ **Automatic Door Control** - Grant access to registered family members  
✅ **Real-Time Notifications** - Instant alerts with photos, date, and time  
✅ **Multi-Camera Support** - Works with phones, IP cameras, and webcams  
✅ **Easy Enrollment** - Simple process to add multiple people  
✅ **Entry Logs** - Complete audit trail with photos and timestamps  
✅ **Firebase Integration** - Cloud storage for face data and notifications  
✅ **Parental Control** - Manual approval required for unknown persons  
✅ **Elder Monitoring** - Track when elderly family members leave/enter  
✅ **Child Safety** - Monitor when children are home alone  

---

## 🎯 Use Case

### Primary Scenario
**Parents are away, child stayed home alone:**

1. **Someone approaches the front door**
2. **Camera detects face** (phone camera, IP camera, or doorbell cam)
3. **System identifies the person:**
   - ✅ **Known Family Member** → Door opens automatically
   - ⚠️ **Known Guest** → Notification sent, door stays locked
   - ❌ **Unknown Person** → Alert sent to parents, door locked
4. **Parents receive notification** with:
   - Photo of the person
   - Date and time
   - Location (which door)
   - Recognition confidence
5. **For unknown persons:** Parents can approve/deny entry remotely
6. **Entry is logged** in the app for review

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Any camera (smartphone, IP camera, doorbell camera, webcam)
- Firebase account (free tier works)
- Internet connection

### Installation (5 Minutes)

```bash
# Clone repository
git clone https://github.com/yourusername/SafeHome.git
cd SafeHome

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with Firebase credentials

# Initialize database
flask db upgrade

# Run application
python SafeHome.py
```

### Access the Application
- 🌐 **Web Dashboard:** http://localhost:5000
- 📱 **Mobile Access:** Use your phone's browser to add it as a camera

---

## 📱 Firebase Integration

### Why Firebase?

1. **Face Recognition Data Storage**
   - Store face encodings (128-dimensional vectors)
   - Cloud backup of enrolled persons
   - Sync across multiple devices

2. **Push Notifications**
   - Firebase Cloud Messaging (FCM)
   - Instant alerts with rich media (photos)
   - Works even when app is closed

3. **Realtime Database**
   - Live entry/exit logs
   - Instant sync across all devices
   - Offline support with automatic sync

### Firebase Setup (10 Minutes)

1. **Create Firebase Project**
   ```
   - Go to https://console.firebase.google.com
   - Click "Add project"
   - Name it "SafeHome"
   - Enable Google Analytics (optional)
   ```

2. **Enable Services**
   ```
   - Realtime Database → Create database
   - Cloud Storage → Enable storage
   - Cloud Messaging → Enable FCM
   - Authentication → Enable Email/Password
   ```

3. **Get Credentials**
   ```
   - Project Settings → Service Accounts
   - Generate new private key
   - Download JSON file → Save as firebase-credentials.json
   ```

4. **Configure Environment**
   ```bash
   # Add to .env file
   FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
   FIREBASE_DATABASE_URL=https://safehome-xxxxx.firebaseio.com
   FIREBASE_STORAGE_BUCKET=safehome-xxxxx.appspot.com
   ```

---

## 🎥 Camera Setup

### Option 1: Phone Camera (Recommended)
```
1. Open SafeHome in phone browser
2. Allow camera permission
3. Select "Add Mobile Camera"
4. Name it (e.g., "Front Door")
5. Enable "Face Detection"
6. Mount phone at entrance
```

### Option 2: IP Camera
```
1. Go to Cameras page
2. Click "Add Camera"
3. Enter:
   - Name: "Front Door"
   - Type: IP Camera
   - RTSP URL: rtsp://username:password@camera-ip:554/stream
   - Enable Face Detection
4. Save and test
```

### Option 3: Webcam/USB Camera
```
1. Connect webcam to computer/Raspberry Pi
2. Add camera with type "USB"
3. Select device number (usually 0)
4. Enable face detection
```

---

## 👨‍👩‍👧‍👦 Adding People

### Enrolling Family Members

**Simple Method:**
```
1. Go to "People" page
2. Click "Add Person"
3. Enter details:
   - Name: "John Doe"
   - Relation: Family
   - Status: Resident (can open doors)
4. Upload 4-6 clear photos:
   - Front view (straight)
   - Left side (25° angle)
   - Right side (25° angle)
   - Smiling
   - Different lighting
5. Click "Enroll"
6. System confirms: "John enrolled with 5 face encodings"
```

**Bulk Enrollment:**
```
1. Prepare photos in folder structure:
   /photos
     /john_doe
       - photo1.jpg
       - photo2.jpg
       - photo3.jpg
     /jane_doe
       - photo1.jpg
       - photo2.jpg
2. Go to "Bulk Enroll"
3. Select folder
4. Confirm names and relations
5. Process all at once
```

### Photo Requirements

✅ **Good Photos:**
- Face clearly visible
- Good lighting (natural daylight)
- Face fills 50-70% of image
- Multiple angles
- Different expressions
- No sunglasses or hats

❌ **Avoid:**
- Blurry images
- Dark or shadowed faces
- Multiple people in one photo
- Heavy filters or makeup
- Very far away shots

---

## 📲 Notification System

### Push Notifications (via Firebase)

**What You'll Receive:**
```json
{
  "title": "Unknown Person at Front Door",
  "body": "Unrecognized face detected",
  "image_url": "https://firebase.../face_image.jpg",
  "timestamp": "2026-02-13 14:30:25",
  "camera_location": "Front Door",
  "confidence": "Unknown",
  "actions": [
    "Approve Entry",
    "Deny Entry",
    "View Details"
  ]
}
```

**Notification Types:**
1. **Known Family** (Info)
   - "John entered at Front Door"
   - Photo + timestamp
   - Auto-opened door

2. **Known Guest** (Warning)
   - "Sarah (Guest) at Front Door"
   - Photo + timestamp
   - Manual approval needed

3. **Unknown Person** (Alert)
   - "Unknown person detected!"
   - Photo + timestamp
   - Requires immediate action

### Email Notifications (Backup)

Automatically sent to all registered parents/guardians:
```
Subject: [SafeHome Alert] Unknown Person at Front Door

An unknown person was detected at your Front Door camera.

Time: February 13, 2026 at 2:30 PM
Location: Front Door
Status: Entry Denied (Awaiting Approval)

Photo: [Attached]

Actions:
- Approve Entry: [Link]
- Deny Entry: [Link]
- View Full Details: [Link]
```

---

## 🔐 Security Features

### Access Control Logic

```mermaid
graph TD
    A[Person Approaches Door] --> B[Camera Detects Face]
    B --> C{Recognize Face?}
    C -->|Yes - Family| D[✅ Open Door Automatically]
    C -->|Yes - Guest| E[⚠️ Notify Parents + Lock]
    C -->|No - Unknown| F[🚨 Alert + Lock + Photo]
    D --> G[Log Entry]
    E --> H{Parent Approves?}
    F --> H
    H -->|Yes| I[Open Door]
    H -->|No| J[Keep Locked]
    I --> G
    J --> G
```

### Recognition Confidence Levels

| Confidence | Action | Description |
|------------|--------|-------------|
| **≥ 0.90** | Auto Open | Very confident match, door opens |
| **0.70-0.89** | Notify | Good match, notify for verification |
| **< 0.70** | Alert | Poor match, treat as unknown |

### User Roles

1. **Admin** (Parents/Guardians)
   - Full system access
   - Approve/deny entry
   - Add/remove people
   - View all logs
   - Configure settings

2. **Resident** (Family Members)
   - Automatic door access
   - Can view own entry logs
   - Limited settings access

3. **Guest** (Registered Visitors)
   - No automatic access
   - Require approval each time
   - Temporary enrollment

---

## 📊 Entry Logs & Monitoring

### Dashboard View

**Real-Time Stats:**
```
Today's Activity
├─ Total Entries: 12
├─ Family Members: 8
├─ Known Guests: 2
├─ Unknown Attempts: 2
└─ Door Opens: 10
```

**Recent Activity:**
```
2:30 PM - Unknown Person - Front Door - ❌ Denied
2:15 PM - John Doe (Family) - Front Door - ✅ Opened
1:45 PM - Sarah Smith (Guest) - Back Door - ⏳ Pending
```

### Entry Log Details

Each entry includes:
- **Photo** of the person
- **Name** (if recognized)
- **Timestamp** (date and time)
- **Location** (which camera/door)
- **Recognition Confidence**
- **Action Taken** (opened/denied/pending)
- **Approved By** (if manual approval)

### Filtering & Search

```
- Filter by date range
- Search by person name
- Filter by location (door)
- Filter by status (approved/denied)
- Export to CSV/PDF
```

---

## 📈 Analytics

### Weekly Summary
```
This Week's Report (Feb 5-11, 2026)
├─ Total Entries: 68
├─ Busiest Day: Monday (15 entries)
├─ Peak Time: 3:00-4:00 PM
├─ Most Active Door: Front Door
└─ Unknown Attempts: 3
```

### Monthly Patterns
```
- Entry/exit patterns
- Time-based analysis
- Person-specific activity
- Security incidents
- System uptime
```

---

## 🛠️ Configuration

### System Settings

```python
# Face Recognition
FACE_RECOGNITION_THRESHOLD = 0.6  # Lower = stricter
MIN_FACE_SIZE = 50  # Minimum pixels
MAX_FACES_PER_FRAME = 5

# Door Control
AUTO_OPEN_RESIDENTS = True
AUTO_OPEN_DURATION = 5  # seconds
REQUIRE_APPROVAL_FOR_GUESTS = True

# Notifications
ENABLE_PUSH_NOTIFICATIONS = True
ENABLE_EMAIL_NOTIFICATIONS = True
NOTIFICATION_QUIET_HOURS = "22:00-07:00"

# Cameras
CAMERA_FRAME_RATE = 10  # FPS
CAMERA_RESOLUTION = "1280x720"
ENABLE_MOTION_DETECTION = True
```

### Door Hardware Integration

**Supported Smart Locks:**
- August Smart Lock
- Yale Assure Lock
- Schlage Encode
- Kwikset Halo
- Generic Z-Wave locks
- Generic WiFi-enabled locks

**Connection Methods:**
- WiFi (recommended)
- Bluetooth
- Z-Wave/Zigbee hub
- HTTP API

---

## 🔧 Troubleshooting

### Face Not Recognized
```
Solutions:
1. Add more photos (4-6 minimum)
2. Use better lighting
3. Take photos from multiple angles
4. Lower the recognition threshold
5. Re-enroll with clearer photos
```

### Camera Connection Issues
```
Solutions:
1. Check WiFi signal strength
2. Verify camera URL/credentials
3. Restart camera device
4. Check firewall settings
5. Update camera firmware
```

### Notifications Not Received
```
Solutions:
1. Check Firebase FCM setup
2. Verify device token registered
3. Enable notifications in phone settings
4. Check spam folder (email)
5. Test notification manually
```

### Door Not Opening
```
Solutions:
1. Check smart lock connection
2. Verify lock status in app
3. Test manual open command
4. Check lock battery level
5. Verify WiFi connectivity
```

---

## 📱 Mobile App (Future)

### Planned Features
- Native iOS/Android apps
- Faster push notifications
- Live camera viewing
- Two-way audio communication
- Geofencing automation
- Offline face recognition

---

## 🛡️ Privacy & Security

### Data Storage
- Face encodings stored locally + Firebase backup
- Photos stored in Firebase Storage (encrypted)
- Entry logs in Realtime Database
- No third-party access

### Data Retention
- Face encodings: Indefinite (until removed)
- Photos: 30 days (configurable)
- Entry logs: 90 days (configurable)
- Deleted data: Permanently removed

### Compliance
- GDPR compliant
- Right to delete data
- Data export available
- Audit logs maintained

---

## 💻 System Requirements

### Minimum
- CPU: Dual-core 1.5 GHz
- RAM: 2 GB
- Storage: 10 GB
- Network: 5 Mbps upload

### Recommended
- CPU: Quad-core 2.0 GHz
- RAM: 4 GB
- Storage: 20 GB SSD
- Network: 10 Mbps upload

### Camera Requirements
- Resolution: 720p minimum (1080p recommended)
- Frame Rate: 10 FPS minimum
- Network: WiFi or Ethernet
- Power: USB or PoE

---

## 📞 Support

### Documentation
- 📖 [Build & Implementation Guide](BUILD_AND_IMPLEMENTATION.md)
- 🏗️ [Architecture & Diagrams](ARCHITECTURE_AND_DIAGRAMS.md)
- 🔧 [API Documentation](http://localhost:5000/api/docs)

### Getting Help
- 💬 GitHub Issues: Report bugs
- 📧 Email: support@safehome.local
- 💬 Community Forum: Coming soon

---

## 🤝 Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Submit a pull request

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- **face_recognition** library by Adam Geitgey
- **Firebase** for cloud services
- **Flask** framework
- **OpenCV** for computer vision
- Open source community

---

**SafeHome v2.0 - Keep your family safe, smart, and secure. 🏠🔐**

*Last Updated: February 13, 2026*
