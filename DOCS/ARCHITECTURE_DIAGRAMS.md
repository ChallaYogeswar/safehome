# SafeHome Face Recognition - System Architecture & Flow Diagrams

## 1. Overall System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SAFEHOME ECOSYSTEM                          │
└─────────────────────────────────────────────────────────────────────┘

                          MOBILE DEVICES
                        ┌──────────────┐
                        │  Phone 1     │
                        │  (Camera)    │
                        └──────┬───────┘
                               │ WebRTC
                               │
    CAMERAS                    │
┌─────────────┐              ┌─┴──────────────────────┐
│ Front Door  ├─┐            │                        │
│ (RTSP)      │ │            │   SAFEHOME SERVER      │
└─────────────┘ │     ┌──────┤                        │
                │─────┤ Face │  ┌──────────────────┐  │
┌─────────────┐ │     │ Recog│  │ FR Service       │  │
│ Back Door   ├─┤     │      │  │ - Encoding       │  │
│ (MJPEG)     │ │     │      │  │ - Matching       │  │
└─────────────┘ │     │      │  │ - Decision       │  │
                │─────┤      │  └──────────────────┘  │
┌─────────────┐ │     └──────┤                        │
│ Garage      ├─┘             │  ┌──────────────────┐ │
│ (HTTP)      │               │  │ Database         │ │
└─────────────┘               │  │ - FacePerson     │ │
                              │  │ - FaceEncoding   │ │
                              │  │ - AccessLog      │ │
                              │  └──────────────────┘ │
                              │                        │
                              │  ┌──────────────────┐ │
                              │  │ WebRTC Manager   │ │
                              │  │ - Signaling      │ │
                              │  │ - Stream Routing │ │
                              │  └──────────────────┘ │
                              └────────────────────────┘
                                       │
                                       │
                              ┌────────┴────────┐
                              │                 │
                        ┌─────▼─────┐  ┌──────▼──────┐
                        │   DOOR    │  │   ALERTS   │
                        │ OPENER    │  │  (Email)   │
                        └───────────┘  └────────────┘
```

---

## 2. Face Recognition Flow

```
CAMERA CAPTURE
      │
      ▼
┌──────────────────┐
│  Detect Face(s)  │  ◄─── dlib detector
│  (dlib CNN)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────────┐
│  Extract Encoding    │  ◄─── 128-dim vector
│  (face_recognition)  │       for each face
└────────┬─────────────┘
         │
         ▼
┌──────────────────────────┐
│  Compare Against DB      │
│  Find Closest Match      │  ◄─── All enrolled persons
└────────┬─────────────────┘       Check distance
         │
         ▼
    ┌─────────────────┐
    │ Distance < 0.6? │
    └────┬────────┬───┘
         │        │
      YES│        │NO
         │        │
    ┌────▼──┐   ┌─▼────────┐
    │KNOWN  │   │ UNKNOWN  │
    │PERSON │   │ PERSON   │
    └────┬──┘   └─┬────────┘
         │        │
    ┌────▼────────▼────┐
    │ Is Resident?    │
    └────┬────────┬───┘
         │        │
      YES│        │NO
         │        │
    ┌────▼──┐   ┌─▼─────────────────┐
    │OPEN   │   │ SEND ALERT        │
    │DOOR   │   │ (Guest/Unknown)   │
    └───────┘   └───────────────────┘
         │                │
         └────────┬───────┘
                  │
                  ▼
          ┌──────────────┐
          │  LOG ACCESS  │
          │  + Timestamp │
          │  + Image     │
          │  + Decision  │
          └──────────────┘
```

---

## 3. Face Enrollment Flow

```
USER SELECTS IMAGES
      │
      ▼
┌──────────────────────┐
│  Load Image Files    │  ◄─── Min 2, Recommended 4-6
│  (PNG/JPG)          │
└─────────┬────────────┘
          │
          ▼
     FOR EACH IMAGE
    ┌──────────────────┐
    │ Detect Face(s)   │  ◄─── Skip if no face
    │ Extract Encoding │
    └────────┬─────────┘
             │
             ▼
    ┌─────────────────────┐
    │ Store Encoding      │  ◄─── 128-dim vector
    │ + Image Path        │
    │ + Timestamp         │
    └────────┬────────────┘
             │
             ▼
    ┌─────────────────┐
    │ Encoding Count  │
    │ >= MIN (2)?     │
    └──┬───────────┬──┘
       │           │
     YES│          │NO
       │           │
     ✓ │           ├─ ✗ REJECT
       │           │  (Need more photos)
       ▼           ▼
    ┌─────────────────────┐
    │  Create FacePerson  │
    │  - Name             │
    │  - Relation         │
    │  - Is_resident      │
    │  - Profile_image    │
    └────────┬────────────┘
             │
             ▼
    ┌─────────────────────┐
    │  Person Enrolled    │
    │  ✓ Success          │
    │  ID: 123            │
    │  Encodings: 5       │
    └─────────────────────┘
```

---

## 4. Access Control Decision Tree

```
FACE DETECTED AT ENTRY
      │
      ▼
  ┌─────────────┐
  │  RECOGNIZE  │
  └──────┬──────┘
         │
    ┌────┴─────────────────┐
    │                      │
 KNOWN                  UNKNOWN
    │                      │
    ▼                      ▼
IS RESIDENT?          ┌──────────┐
    │                 │ CHECK    │
    ├─────┬───────┐   │ PREVIOUS │
    │     │       │   │ ATTEMPTS │
   YES   NO       ?   └──────────┘
    │     │       │
    │     │    MAYBE
    │     │    (Low Conf)
    │     │       │
    ▼     ▼       ▼
  OPEN  ALERT  REVIEW
  DOOR  OWNER  MANUALLY
    │     │       │
    │     │       │
    └─────┴───────┘
         │
         ▼
    ┌──────────────┐
    │  LOG ACCESS  │
    │  + Decision  │
    │  + Timestamp │
    └──────────────┘
    
LOG CONTENTS:
├─ DOOR_OPENED (Resident)
├─ ALERT_SENT (Guest)
├─ ALERT_SENT (Unknown)
└─ DOOR_DENIED (Threat)
```

---

## 5. Multi-Camera Real-time Processing

```
CAMERA 1               CAMERA 2               CAMERA 3
(Front Door)           (Mobile)               (Back Door)
    │                      │                      │
    │                      │                      │
    ├──────────────────────┼──────────────────────┤
                           │
                    ┌──────▼───────┐
                    │ FRAME POOL   │
                    │ Processing   │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
    ┌────────┐        ┌────────┐        ┌────────┐
    │ FR-1   │        │ FR-2   │        │ FR-3   │
    │Engine  │        │Engine  │        │Engine  │
    └────┬───┘        └────┬───┘        └────┬───┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Access Log   │
                    │ (All Results)│
                    └──────────────┘

BENEFITS:
- Parallel processing
- Independent decisions per camera
- All logged in one place
- Real-time updates to dashboard
```

---

## 6. Mobile Camera WebRTC Flow

```
MOBILE PHONE               SAFEHOME SERVER
(Your Device)              (Signaling Server)

  getUserMedia()
       │
       ▼
  RTCPeerConnection
       │
       ├─ create offer
       │       │
       │       ▼
       │  emit('webrtc:offer')
       │       │
       ├───────┤
       │       │
       │       ▼
       │  Receive answer
       │ ◄─ emit('webrtc:answer')
       │       │
       ├───────┘
       │
       ▼
  P2P Connection
  Established
       │
       ▼
  ┌─────────────┐
  │  Send Offer │
  │   ICE       │
  │ Candidates  │  ◄─ For NAT traversal
  └────────────┘
       │
       ▼
  Video Stream
  (H264/VP8)
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
    LOCAL            ALL VIEWERS
    DISPLAY          (Dashboard)
       │                 │
       └─────────────────┘
              │
              ▼
         Frame Processing
         (Face Recognition)
```

---

## 7. Database Relationship Diagram

```
┌──────────────┐
│    User      │ (authenticated user)
│              │
│ - id         │
│ - username   │
│ - email      │
└──────┬───────┘
       │ 1:N
       │
   ┌───┴──────────────────────────────┐
   │                                  │
   ▼                                  ▼
┌──────────────┐                ┌──────────────┐
│   Camera     │                │ FacePerson   │
│              │                │              │
│ - id         │                │ - id         │
│ - name       │                │ - name       │
│ - location   │                │ - relation   │
│ - access_ctl │                │ - resident   │
└──────┬───────┘                └──────┬───────┘
       │                              │ 1:N
       │ 1:N                         │
       │                              ▼
       │                        ┌──────────────┐
       │                        │FaceEncoding  │
       │                        │              │
       │                        │ - encoding[] │
       │                        │ - image_path │
       │                        └──────────────┘
       │
       │
       ▼
┌──────────────┐
│  AccessLog   │ ◄─ Records all access attempts
│              │
│ - person_id  │ (FK to FacePerson)
│ - person_name│
│ - is_known   │
│ - confidence │
│ - action     │ (door_opened/denied/alert_sent)
│ - timestamp  │
└──────────────┘
```

---

## 8. API Call Sequence Diagram

```
CLIENT                          SERVER

POST /face/enroll
├─ person_name
├─ images[] (multipart)
└────────────────────────────────────────►
                                │
                                ▼
                        Detect faces
                        Extract encodings
                        Validate count >= 2
                        Store to DB
                                │
◄────────────────────────────────────────
│ Response:
│ - person_id
│ - encoding_count
│ - success


POST /face/recognize
├─ camera_id
├─ image (file or base64)
└────────────────────────────────────────►
                                │
                                ▼
                        Extract face
                        Get DB encodings
                        Compare all persons
                        Find best match
                        Create AccessLog
                                │
◄────────────────────────────────────────
│ Response:
│ - is_known
│ - person_name
│ - confidence
│ - relation


Socket.IO: camera:frame
┌───────────────────────────────────────►
│ {camera_id, base64_frame}
│                        │
│                        ▼
│                    Process frame
│                    Detect face
│                    Recognize
│                    Broadcast to viewers
│◄───────────────────────────────────────
│ Emit: camera:frame {frame}
│      (to all watching clients)
└────────────────────────────────────────
```

---

## 9. Enrollment Photo Requirements

```
GOOD ENROLLMENT PHOTOS ✓          BAD ENROLLMENT PHOTOS ✗

┌─────────────────┐               ┌──────────────────┐
│ ┌─────────────┐ │               │ ┌──────────────┐ │
│ │  Front      │ │               │ │   Blurry     │ │
│ │  Straight   │ │               │ │               │ │
│ │ ☺ Smiling  │ │               │ │ (Unusable)   │ │
│ └─────────────┘ │               │ └──────────────┘ │
│ Confidence: 98% │               │ Confidence: 10%  │
└─────────────────┘               └──────────────────┘

┌─────────────────┐               ┌──────────────────┐
│ ┌─────────────┐ │               │ ┌──────────────┐ │
│ │   25° Left  │ │               │ │   Dark/     │ │
│ │   ☺ Natural │ │               │ │   Shadow    │ │
│ │             │ │               │ │             │ │
│ └─────────────┘ │               │ └──────────────┘ │
│ Confidence: 95% │               │ Confidence: 35%  │
└─────────────────┘               └──────────────────┘

BEST PRACTICE PATTERN:
                    Face fills 50-70% of image
                    Multiple angles
                    Different expressions
                    Consistent lighting
                    No obstructions
                    >= 4 photos minimum
```

---

## 10. System Performance Timeline

```
USER ARRIVES AT DOOR

T=0ms    │ Camera detects motion
T=10ms   │ Capture frame
T=50ms   │ ┌─ Detect face (dlib)
T=100ms  │ └─ Extract encoding
T=150ms  │ ┌─ Query database
T=200ms  │ ├─ Compare against 5 persons
T=250ms  │ ├─ Calculate confidence
T=300ms  │ └─ Make decision
T=350ms  │ Store in AccessLog
T=400ms  │ ┌─ DOOR OPENS or ALERT SENT
T=450ms  │ └─ Email notification queued
         │
     Total: ~450ms (0.45 seconds)

This accounts for:
- Real-time processing
- Database access
- Network latency
- Email queuing
```

---

## 11. Scalability Architecture

```
CURRENT (Single Server)

┌──────────────────────────┐
│  SAFEHOME SINGLE SERVER  │
│ ┌────────────────────┐   │
│ │ Flask App          │   │
│ │ - All routes       │   │
│ │ - All logic        │   │
│ │ - All processing   │   │
│ └────────────────────┘   │
│          │                │
│ ┌────────▼────────┐       │
│ │ SQLite/PostgreSQL        │
│ │ - All data       │       │
│ └──────────────────┘       │
└──────────────────────────┘

Handles: 100+ persons, 10+ cameras ✓


FUTURE (Scaled Architecture)

┌─────────────────────────────────────────────────────┐
│              LOAD BALANCER (nginx)                  │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────▼───┐   ┌────▼───┐  ┌────▼───┐
   │ App 1  │   │ App 2  │  │ App 3  │
   │(FR)    │   │(FR)    │  │(FR)    │
   └────┬───┘   └────┬───┘  └────┬───┘
        │            │           │
        └────────────┼───────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
   ┌────▼────┐             ┌─────▼────┐
   │PostgreSQL│            │  Redis   │
   │ (Data)   │            │(Cache)   │
   └──────────┘            └──────────┘

Handles: 1000+ persons, 100+ cameras ✓
```

---

## 12. Security & Audit Flow

```
ACCESS ATTEMPT
      │
      ▼
┌──────────────────┐
│ Detect Face      │
│ Extract Vector   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Compare to DB    │
│ Calculate Score  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Make Decision    │
│ - Resident       │
│ - Guest          │
│ - Unknown        │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────┐
│ CREATE ACCESS LOG ENTRY:     │
│ - Camera ID                  │
│ - Person ID (if known)       │
│ - Person Name                │
│ - Is Known (T/F)             │
│ - Confidence Score           │
│ - Face Image                 │
│ - Access Granted (T/F)       │
│ - Action Taken               │
│ - UTC Timestamp              │
│ - IP Address                 │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ SECURITY AUDIT READY:        │
│ - Searchable by camera       │
│ - Searchable by person       │
│ - Searchable by date range   │
│ - Exportable for reports     │
│ - Immutable records          │
└──────────────────────────────┘
```

---

These diagrams illustrate:
1. Overall system architecture
2. Face recognition processing flow
3. Enrollment process
4. Access control decisions
5. Multi-camera processing
6. WebRTC mobile integration
7. Database relationships
8. API sequences
9. Photo quality requirements
10. Performance timeline
11. Scalability options
12. Security & audit trail

