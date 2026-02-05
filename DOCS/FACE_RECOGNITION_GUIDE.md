# SafeHome Face Recognition & Multi-Camera Integration Guide

## Overview

SafeHome now includes advanced face recognition for access control and multi-camera support including mobile phone integration via WebRTC.

### Features
- **Face Enrollment**: Register known persons with multiple photos
- **Access Control**: Automatically open doors for recognized residents
- **Unknown Detection**: Alert on unknown persons
- **Mobile Camera Support**: Stream from your phone's camera
- **Multiple Cameras**: Monitor multiple cameras simultaneously
- **Real-time Recognition**: Face detection on camera streams
- **Access Logging**: Complete audit trail of all access attempts

---

## Architecture

### Backend Components

#### 1. Face Recognition Service (`app/services/face_recognition_service.py`)
- **Face Encoding**: Converts images to 128-dimensional vectors
- **Face Matching**: Compares detected faces against enrolled persons
- **Similarity Threshold**: 0.6 (configurable) - lower = stricter matching
- **Multiple Encodings**: Each person can have multiple face encodings for better recognition

#### 2. Camera Stream Manager (`app/services/camera_stream_manager.py`)
- **WebRTC Support**: Peer-to-peer connections for mobile cameras
- **Frame Broadcasting**: Real-time streaming to multiple viewers
- **ICE Candidates**: NAT traversal for mobile connections
- **Stream Registry**: Tracks active cameras and connected clients

#### 3. Face Routes (`app/routes/face.py`)
- Enrollment endpoints
- Recognition endpoints
- Access logging
- Statistics

### Database Models

```
User
  ├── Camera (has access_control_enabled, face_detection_enabled)
  │   ├── Detection
  │   └── AccessLog
  │
  ├── FacePerson (enrolled persons)
  │   └── FaceEncoding (128-dim vectors)
  │
  └── SecurityLog
```

---

## API Endpoints

### Face Enrollment

#### Enroll a New Person
```
POST /face/enroll
Content-Type: multipart/form-data

Form Data:
- person_name: string (required)
- relation: string (optional: 'family', 'guest', 'staff', default: 'family')
- is_resident: boolean (optional, default: true) - can they open doors?
- images: file[] (required, minimum 2 images)

Response:
{
  "success": true,
  "message": "Successfully enrolled John with 3 face encodings",
  "person_id": 1,
  "encoding_count": 3
}
```

#### List Enrolled Persons
```
GET /face/enrolled

Response:
{
  "success": true,
  "persons": [
    {
      "id": 1,
      "name": "John Doe",
      "relation": "family",
      "is_resident": true,
      "profile_image": "uploads/faces/...",
      "encoding_count": 3,
      "recognition_count": 15,
      "last_recognized": "2026-02-05T10:30:00Z"
    }
  ]
}
```

#### Delete Enrolled Person
```
DELETE /face/enrolled/{person_id}

Response:
{
  "success": true,
  "message": "Deleted John Doe from enrollment"
}
```

### Face Recognition

#### Recognize a Face
```
POST /face/recognize
Content-Type: multipart/form-data

Form Data:
- camera_id: integer (required)
- image: file (required) OR image_data: base64 string

Response:
{
  "success": true,
  "recognition": {
    "is_known": true,
    "person_id": 1,
    "person_name": "John Doe",
    "confidence": 0.95,
    "relation": "family",
    "is_resident": true
  },
  "image_path": "uploads/faces/..."
}
```

### Access Control

#### Enable Access Control on Camera
```
POST /face/camera/{camera_id}/enable-access-control

Response:
{
  "success": true,
  "message": "Access control enabled",
  "camera": {
    "id": 1,
    "name": "Front Door",
    "access_control_enabled": true,
    "face_detection_enabled": true
  }
}
```

#### Get Access Logs
```
GET /face/access-log?camera_id=1&limit=50&offset=0

Response:
{
  "success": true,
  "total": 150,
  "logs": [
    {
      "id": 1,
      "camera_id": 1,
      "person_name": "John Doe",
      "is_known": true,
      "confidence": 0.95,
      "access_granted": true,
      "action": "door_opened",
      "timestamp": "2026-02-05T10:30:00Z",
      "image_path": "..."
    }
  ]
}
```

#### Get Statistics
```
GET /face/stats

Response:
{
  "success": true,
  "stats": {
    "enrolled_persons": 5,
    "total_encodings": 15,
    "access_granted_count": 120,
    "unknown_persons_count": 3,
    "recent_access": [...]
  }
}
```

---

## Mobile Camera Integration

### How It Works

1. **Mobile Camera** (your phone) captures video
2. **WebRTC Connection** established peer-to-peer
3. **Frames Streamed** to SafeHome server in real-time
4. **Face Detection** performed on each frame
5. **Recognition** matches against enrolled persons
6. **Access Granted/Denied** based on match

### Setup Mobile Camera

#### Using Web Browser
```
1. Go to http://safehome-ip:5000/camera
2. Click "Add Mobile Camera"
3. Allow camera permission
4. Camera stream starts automatically
5. Select "Enable Access Control" for door detection
```

#### Using Mobile App (coming soon)
```
- Download SafeHome mobile app
- Register mobile device as camera
- Enable continuous monitoring
- Get push notifications for unknown persons
```

### Socket.IO Events for Mobile Camera

#### Camera Registration
```javascript
socket.emit('camera:register', {
  camera_id: 1,
  user_id: 123,
  stream_type: 'mobile'
});

socket.on('camera:registered', (data) => {
  console.log('Camera registered:', data);
});
```

#### Send Frame for Processing
```javascript
socket.emit('camera:frame', {
  camera_id: 1,
  frame: base64EncodedImage
});
```

#### WebRTC Offer (P2P Video)
```javascript
socket.emit('webrtc:offer', {
  camera_id: 1,
  offer: peerConnection.localDescription.sdp
});

socket.on('webrtc:answer', (data) => {
  peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
});
```

---

## Multi-Camera Setup

### Scenario 1: Multiple Fixed Cameras
```
- Front Door Camera (RTSP)
- Back Door Camera (MJPEG)
- Garage Camera (HTTP)

All with face recognition and access control
```

### Scenario 2: Fixed + Mobile Cameras
```
- Front Door Camera (fixed, RTSP)
- Mobile Camera 1 (your phone, WiFi)
- Mobile Camera 2 (family member's phone, mobile data)

All streams visible on dashboard
```

### Scenario 3: Multi-Location
```
Location 1 (Home):
  - Front Door (fixed)
  - Mobile phone

Location 2 (Office):
  - Entrance (fixed)
  - Mobile phone

All synchronized in one account
```

---

## Access Control Logic

### Decision Tree

```
Detected Face
    ↓
[Face Recognition]
    ↓
Is Known?
    ├─ YES
    │   ├─ Is Resident?
    │   │   ├─ YES → OPEN DOOR ✓
    │   │   └─ NO  → SEND ALERT (guest/staff)
    │   └─ Log with HIGH confidence
    │
    └─ NO
        ├─ Send ALERT (unknown person)
        ├─ Log as SECURITY EVENT
        ├─ Store image
        └─ Keep DOOR CLOSED
```

### Confidence Thresholds

- **>= 0.9**: Very confident match (automatic access)
- **0.7 - 0.9**: Good match (manual review recommended)
- **< 0.7**: Poor match (treated as unknown)

---

## Face Enrollment Best Practices

### Capturing Good Enrollment Photos

#### Requirements
- **Minimum 2 photos** per person (recommended: 4-6)
- **Well lit** (natural light preferred)
- **Multiple angles**: front, slightly left, slightly right
- **Various distances**: face fills 50-70% of image
- **Clear face**: no occlusions, sunglasses, hats
- **Different expressions**: neutral and smiling
- **Different head positions**: looking straight, slightly up/down

#### Bad Examples ❌
- Blurry photos
- Face in shadow
- Multiple people in image
- Photos with filters
- Very far away (face too small)
- Wearing heavy makeup/disguise

### Sample Commands

```bash
# Enroll person with curl
curl -X POST http://localhost:5000/face/enroll \
  -F "person_name=John Doe" \
  -F "relation=family" \
  -F "is_resident=true" \
  -F "images=@photo1.jpg" \
  -F "images=@photo2.jpg" \
  -F "images=@photo3.jpg"
```

---

## Real-World Scenarios

### Scenario: Family Home Access

```
Setup:
1. Enroll 4 family members
   - John (resident)
   - Jane (resident)
   - Child 1 (resident)
   - Child 2 (resident)

2. Enable access control on:
   - Front door camera
   - Back door camera

3. Disable for:
   - Internal cameras
   - Garage camera

When John approaches:
→ Face detected
→ Recognized as John (confidence: 0.97)
→ John is resident
→ DOOR AUTOMATICALLY OPENS ✓
→ Access logged

When unknown person approaches:
→ Face detected
→ Not recognized
→ ALERT sent to all users
→ Image saved
→ Door REMAINS CLOSED
→ Email notification sent
```

### Scenario: Office Entry

```
Setup:
1. Enroll employees (is_resident: true)
2. Enroll visitors (is_resident: false)
3. Enable access control on entrance

Guest arrival:
→ Face recognized as registered guest
→ ALERT sent to security
→ Door stays closed (manual approval needed)
→ When admin approves: door opens
```

### Scenario: Traveling with Multiple Cameras

```
Setup:
1. Your home (3 cameras):
   - Enroll family members
   - All access control enabled

2. Business trip to hotel:
   - Enable mobile phone camera
   - Temporary guest access enabled
   - Monitor home in real-time

3. Partner at home:
   - Uses their mobile camera
   - Both streams visible
   - Can recognize each other for access
```

---

## Performance & Optimization

### Face Recognition Speed

| Operation | Speed | Notes |
|-----------|-------|-------|
| Encode image (1 face) | ~0.3s | One-time during enrollment |
| Recognize face | ~0.1s | Compare against 100 encodings |
| Full pipeline | ~0.5s | Detect + recognize + log |

### Bandwidth

- **Mobile camera H264 stream**: 2-5 Mbps (depends on resolution)
- **Frame upload for recognition**: 50-200 KB
- **Multiple streams**: Add per stream

### Database

- **Per person**: ~20 KB (3-5 face encodings)
- **Per access log**: ~1 KB
- **1000 access logs**: ~1 MB

---

## Troubleshooting

### Issue: Face not recognized
```
Solutions:
1. Take clearer enrollment photos
2. Ensure good lighting
3. Add more enrollment images
4. Check confidence threshold (lower it slightly)
5. Different angles in enrollment
```

### Issue: False positives
```
Solutions:
1. Increase confidence threshold
2. Better enrollment photos (more distinct)
3. Reduce number of similar persons
4. Manual review before access
```

### Issue: Mobile camera lagging
```
Solutions:
1. Check WiFi/network strength
2. Lower video resolution
3. Reduce frame rate
4. Use 5GHz WiFi if available
5. Check device temperature (may throttle)
```

### Issue: WebRTC connection fails
```
Solutions:
1. Check firewall/NAT
2. Enable STUN/TURN servers
3. Verify CORS configuration
4. Try different network (cellular)
5. Update browser/device
```

---

## Configuration

### Environment Variables

```bash
# Face Recognition
FACE_MATCH_TOLERANCE=0.6              # Lower = stricter
MIN_FACE_ENCODINGS=2                  # Minimum for enrollment

# Camera Stream
CAMERA_FRAME_RATE=15                  # FPS for processing
CAMERA_MAX_RESOLUTION=1280x720        # For mobile

# WebRTC
WEBRTC_STUN_SERVERS=stun.l.google.com:19302
WEBRTC_TURN_SERVER=                   # Optional TURN server
```

### Database Configuration

```python
# In config.py
FACE_RECOGNITION_CONFIG = {
    'MODEL': 'hog',  # 'hog' (fast) or 'cnn' (accurate)
    'TOLERANCE': 0.6,
    'MIN_ENCODINGS': 2,
    'MAX_FACES_PER_FRAME': 5
}
```

---

## Security Considerations

### Privacy
- Face images stored only locally
- No cloud face data
- Automatic deletion options available
- User-controlled retention policy

### Safety
- Access logs auditable
- Email alerts on access
- Stranger alerts configurable
- Can disable access remotely

### Best Practices
- Use strong device passwords
- Enable two-factor authentication
- Regularly review access logs
- Update software regularly
- Back up enrollment data

---

## Future Enhancements

- [ ] Mobile app with push notifications
- [ ] Behavior-based anomaly detection
- [ ] Thermal camera support (detect fever)
- [ ] Voice recognition for authorization
- [ ] Age/gender detection
- [ ] Crowd detection
- [ ] Integration with smart locks
- [ ] Integration with lighting/HVAC

---

## API Quick Reference

```bash
# Enroll person
curl -X POST http://localhost:5000/face/enroll \
  -F "person_name=John" -F "images=@photo.jpg"

# List enrolled
curl http://localhost:5000/face/enrolled

# Recognize face
curl -X POST http://localhost:5000/face/recognize \
  -F "camera_id=1" -F "image=@test.jpg"

# Enable access control
curl -X POST http://localhost:5000/face/camera/1/enable-access-control

# Get access logs
curl "http://localhost:5000/face/access-log?camera_id=1&limit=10"

# Get stats
curl http://localhost:5000/face/stats
```

---

## Support & Documentation

For more information:
- Face Recognition: https://face-recognition.readthedocs.io/
- WebRTC: https://webrtc.org/
- Socket.IO: https://socket.io/docs/
- SafeHome Wiki: `/docs/wiki`
