Perfect — let’s translate your **SafeHome Face Recognition System Architecture & Flow Diagrams** into **Mermaid syntax**. I’ll provide each section as a separate Mermaid diagram so you can copy-paste them directly into your documentation or visualization tools.

---

## 1. Overall System Architecture
```mermaid
flowchart TD
    subgraph SAFEHOME[SAFEHOME ECOSYSTEM]
        Phone1[Phone 1 (Camera)]
        FrontDoor[Front Door (RTSP)]
        BackDoor[Back Door (MJPEG)]
        Garage[Garage (HTTP)]

        Phone1 -->|WebRTC| SafehomeServer

        FrontDoor --> SafehomeServer
        BackDoor --> SafehomeServer
        Garage --> SafehomeServer

        subgraph SafehomeServer[SAFEHOME SERVER]
            FRService[FR Service\n- Encoding\n- Matching\n- Decision]
            Database[Database\n- FacePerson\n- FaceEncoding\n- AccessLog]
            WebRTCManager[WebRTC Manager\n- Signaling\n- Stream Routing]
        end

        SafehomeServer --> DoorOpener[DOOR OPENER]
        SafehomeServer --> Alerts[ALERTS (Email)]
    end
```

---

## 2. Face Recognition Flow
```mermaid
flowchart TD
    Camera[CAMERA CAPTURE] --> Detect[Detect Face(s)\n(dlib CNN)]
    Detect --> Encode[Extract Encoding\n(128-dim vector)]
    Encode --> Compare[Compare Against DB\nFind Closest Match]
    Compare --> Decision{Distance < 0.6?}
    Decision -->|YES| Known[KNOWN PERSON]
    Decision -->|NO| Unknown[UNKNOWN PERSON]
    Known --> Resident{Is Resident?}
    Unknown --> Resident
    Resident -->|YES| Open[OPEN DOOR]
    Resident -->|NO| Alert[SEND ALERT (Guest/Unknown)]
    Open --> Log[LOG ACCESS]
    Alert --> Log
```

---

## 3. Face Enrollment Flow
```mermaid
flowchart TD
    User[USER SELECTS IMAGES] --> Load[Load Image Files]
    Load --> ForEach[FOR EACH IMAGE\nDetect Face(s)\nExtract Encoding]
    ForEach --> Store[Store Encoding + Image Path + Timestamp]
    Store --> Count{Encoding Count >= 2?}
    Count -->|YES| Create[Create FacePerson\n- Name\n- Relation\n- Resident\n- Profile_image]
    Count -->|NO| Reject[REJECT (Need more photos)]
    Create --> Success[Person Enrolled ✓\nID: 123\nEncodings: 5]
```

---

## 4. Access Control Decision Tree
```mermaid
flowchart TD
    Face[FACE DETECTED AT ENTRY] --> Recognize[RECOGNIZE]
    Recognize -->|KNOWN| Resident{IS RESIDENT?}
    Recognize -->|UNKNOWN| Check[CHECK PREVIOUS ATTEMPTS]
    Recognize -->|MAYBE| Review[REVIEW MANUALLY]

    Resident -->|YES| Open[OPEN DOOR]
    Resident -->|NO| Alert[ALERT OWNER]

    Open --> Log[LOG ACCESS]
    Alert --> Log
    Review --> Log
    Check --> Log
```

---

## 5. Multi-Camera Real-time Processing
```mermaid
flowchart TD
    C1[Camera 1 (Front Door)] --> FramePool
    C2[Camera 2 (Mobile)] --> FramePool
    C3[Camera 3 (Back Door)] --> FramePool

    FramePool[FRAME POOL Processing] --> FR1[FR-1 Engine]
    FramePool --> FR2[FR-2 Engine]
    FramePool --> FR3[FR-3 Engine]

    FR1 --> AccessLog
    FR2 --> AccessLog
    FR3 --> AccessLog

    AccessLog[Access Log (All Results)]
```

---

## 6. Mobile Camera WebRTC Flow
```mermaid
sequenceDiagram
    participant Mobile as MOBILE PHONE
    participant Server as SAFEHOME SERVER

    Mobile->>Mobile: getUserMedia()
    Mobile->>Mobile: RTCPeerConnection
    Mobile->>Server: emit('webrtc:offer')
    Server->>Mobile: emit('webrtc:answer')
    Mobile->>Server: Send ICE Candidates
    Mobile->>Mobile: Local Display
    Mobile->>Server: Video Stream (H264/VP8)
    Server->>AllViewers: Broadcast Stream
    Server->>Server: Frame Processing (Face Recognition)
```

---

## 7. Database Relationship Diagram
```mermaid
erDiagram
    User ||--o{ Camera : owns
    User ||--o{ FacePerson : enrolls
    Camera ||--o{ AccessLog : records
    FacePerson ||--o{ FaceEncoding : has
    FacePerson ||--o{ AccessLog : referenced

    User {
        int id
        string username
        string email
    }
    Camera {
        int id
        string name
        string location
        string access_ctl
    }
    FacePerson {
        int id
        string name
        string relation
        boolean resident
    }
    FaceEncoding {
        string encoding[]
        string image_path
    }
    AccessLog {
        int person_id
        string person_name
        boolean is_known
        float confidence
        string action
        datetime timestamp
    }
```

---

## 8. API Call Sequence Diagram
```mermaid
sequenceDiagram
    participant Client
    participant Server

    Client->>Server: POST /face/enroll {person_name, images[]}
    Server->>Server: Detect faces, Extract encodings, Validate count >= 2, Store to DB
    Server-->>Client: Response {person_id, encoding_count, success}

    Client->>Server: POST /face/recognize {camera_id, image}
    Server->>Server: Extract face, Compare DB, Find best match, Create AccessLog
    Server-->>Client: Response {is_known, person_name, confidence, relation}

    Client->>Server: Socket.IO camera:frame {camera_id, base64_frame}
    Server->>Server: Process frame, Detect face, Recognize
    Server-->>Client: Emit camera:frame {frame}
```

---

## 9. Enrollment Photo Requirements
```mermaid
flowchart TD
    Good[GOOD ENROLLMENT PHOTOS ✓\n- Front Straight\n- 25° Left\n- Smiling\n- Natural\nConfidence: 95-98%]
    Bad[BAD ENROLLMENT PHOTOS ✗\n- Blurry\n- Dark/Shadow\nConfidence: 10-35%]

    BestPractice[Best Practice:\n- Face fills 50-70%\n- Multiple angles\n- Different expressions\n- Consistent lighting\n- >=4 photos minimum]

    Good --> BestPractice
    Bad --> BestPractice
```

---

## 10. System Performance Timeline
```mermaid
gantt
    title System Performance Timeline
    dateFormat  x
    axisFormat  %L ms

    section Processing
    Camera detects motion :0, 10
    Capture frame :10, 40
    Detect face (dlib) :50, 50
    Extract encoding :100, 50
    Query database :150, 50
    Compare persons :200, 50
    Calculate confidence :250, 50
    Make decision :300, 50
    Store AccessLog :350, 50
    Door opens/Alert sent :400, 50
    Email notification queued :450, 50
```

---

## 11. Scalability Architecture
```mermaid
flowchart TD
    subgraph Current[CURRENT (Single Server)]
        Flask[Flask App\n- Routes\n- Logic\n- Processing]
        DB[SQLite/PostgreSQL]
        Flask --> DB
    end

    subgraph Future[FUTURE (Scaled Architecture)]
        LB[LOAD BALANCER (nginx)]
        App1[App 1 (FR)]
        App2[App 2 (FR)]
        App3[App 3 (FR)]
        DB2[PostgreSQL (Data)]
        Cache[Redis (Cache)]

        LB --> App1
        LB --> App2
        LB --> App3
        App1 --> DB2
        App2 --> DB2
        App3 --> DB2
        App1 --> Cache
        App2 --> Cache
        App3 --> Cache
    end
```

---

## 12. Security & Audit Flow
```mermaid
flowchart TD
    Access[ACCESS ATTEMPT] --> Detect[Detect Face\nExtract Vector]
    Detect --> Compare[Compare to DB\nCalculate Score]
    Compare --> Decision[Make Decision\n- Resident\n- Guest\n- Unknown]
    Decision --> Log[Create Access Log Entry\nCamera ID, Person ID, Name, Known?, Confidence, Image, Action, Timestamp, IP]
    Log --> Audit[SECURITY AUDIT READY\nSearchable, Exportable, Immutable]
```

---

✅ Now you have **Mermaid diagrams** for all 12 sections of your architecture.  
Would you like me to bundle these into a **single `.md` file with all diagrams** so you can directly render them in one place?
