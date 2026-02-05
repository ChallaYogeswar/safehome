# SafeHome - Phone Camera Security System

A functional home security application using phone camera for detection with ML-powered alerts and automation.

## Features

### Core Features
- Phone Camera Detection: Use your phone camera for real-time monitoring
- Motion Detection: Background subtraction algorithm
- Object Detection: OpenCV-based object recognition
- Face Detection: Haar Cascade face detection
- Real-time Alerts: WebSocket-based instant notifications
- Automation Rules: Create IF-THIS-THEN-THAT rules
- Analytics Dashboard: Charts and statistics
- Multi-user Support: Secure authentication with MFA

### Security Features
- JWT + Session-based authentication
- Two-factor authentication (TOTP)
- Password hashing (bcrypt)
- Account lockout after failed attempts
- Security event logging
- Role-based access control

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL (for production) or SQLite (for development)
- Redis (for WebSocket and caching)
- Modern web browser with camera access

### Installation

```bash
# Clone repository
git clone <repository-url>
cd SafeHome

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Run application
python SafeHome.py
```

Visit http://localhost:5000

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## Project Structure

```
SafeHome/
├── app/
│   ├── __init__.py              # App factory
│   ├── models.py                # Database models
│   ├── routes/                  # Route blueprints
│   │   ├── auth.py             # Authentication
│   │   ├── camera.py           # Camera management
│   │   ├── dashboard.py        # Main dashboard
│   │   ├── alerts.py           # Alert management
│   │   ├── automation.py       # Automation rules
│   │   └── analytics.py        # Analytics
│   ├── services/                # Business logic
│   │   ├── auth_service.py     # Auth operations
│   │   ├── camera_service.py   # Motion detection
│   │   ├── ml_service.py       # ML inference
│   │   ├── alert_service.py    # Alert creation
│   │   └── rule_engine.py      # Rule evaluation
│   ├── utils/                   # Utilities
│   │   ├── decorators.py       # Custom decorators
│   │   ├── validators.py       # Input validation
│   │   └── constants.py        # Constants
│   ├── static/                  # Static files
│   │   ├── css/
│   │   └── js/
│   └── templates/               # HTML templates
├── ml_models/                   # ML model files
├── uploads/                     # User uploads
├── logs/                        # Application logs
├── config.py                    # Configuration
├── SafeHome.py                  # Entry point
├── requirements.txt             # Dependencies
├── Dockerfile                   # Docker config
└── docker-compose.yml           # Docker Compose
```

## Usage Guide

### 1. Create Account
- Visit /auth/register
- Fill in username, email, password
- Login at /auth/login

### 2. Add Camera
- Go to Cameras page
- Click "Add Camera"
- Enter name and location
- Grant browser camera permission

### 3. Start Detection
- Click "Start" on camera card
- Browser will request camera access
- Detection starts automatically
- Frame processing every 2 seconds

### 4. View Alerts
- Real-time alerts appear as notifications
- Check Alerts page for history
- Mark as read or delete

### 5. Create Automation Rules
- Go to Automation page
- Click "Create Rule"
- Select trigger type
- Choose action
- Rule runs automatically

### 6. View Analytics
- Analytics page shows:
  - Detection trends
  - Alert distribution
  - Top detected objects
  - Camera activity

## API Endpoints

### Authentication
- POST /auth/register - Register user
- POST /auth/login - Login
- GET /auth/logout - Logout
- GET /auth/profile - View profile
- POST /auth/setup-mfa - Setup 2FA

### Cameras
- GET /camera - List cameras
- POST /camera/add - Add camera
- PUT /camera/<id>/update - Update camera
- DELETE /camera/<id>/delete - Delete camera
- POST /camera/<id>/process-frame - Process frame

### Alerts
- GET /alerts - List alerts
- GET /alerts/unread - Get unread
- POST /alerts/<id>/read - Mark as read
- DELETE /alerts/<id>/delete - Delete alert

### Automation
- GET /automation - List rules
- POST /automation/create - Create rule
- PUT /automation/<id>/update - Update rule
- DELETE /automation/<id>/delete - Delete rule
- POST /automation/<id>/toggle - Toggle active

### Analytics
- GET /analytics/detections - Detection stats
- GET /analytics/alerts - Alert stats
- GET /analytics/cameras - Camera stats
- GET /analytics/timeline - Event timeline

## Configuration

Edit `.env` file:

```env
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///safehome_dev.db
REDIS_URL=redis://localhost:6379/0

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

## Development

### Run Tests
```bash
pytest --cov=app
```

### Database Migrations
```bash
flask db migrate -m "Description"
flask db upgrade
```

### Add New Route
1. Create file in `app/routes/`
2. Register blueprint in `app/__init__.py`
3. Add template in `app/templates/`

### Add New Service
1. Create file in `app/services/`
2. Import in routes as needed

## ML Models

### Motion Detection
- Algorithm: Background subtraction
- Threshold: 25 (configurable)
- Min area: 500 pixels

### Object Detection
- Model: Haar Cascade (built-in)
- Can upgrade to YOLO (download weights)
- Place weights in `ml_models/`

### Face Detection
- Model: Haar Cascade frontalface
- Pre-trained, no download needed
- Confidence: 90%

## Security Best Practices

1. Change Default Secrets
   - Update SECRET_KEY in .env
   - Update JWT_SECRET_KEY

2. Use HTTPS in Production
   - Configure SSL certificates
   - Set SESSION_COOKIE_SECURE=True

3. Enable MFA
   - Setup 2FA for admin accounts
   - Use strong passwords

4. Regular Backups
   - Backup database regularly
   - Store logs securely

## Troubleshooting

### Camera Not Working
- Check browser permissions
- Ensure HTTPS (required for camera access)
- Try different browser

### No Alerts Received
- Check Redis connection
- Verify WebSocket connection in browser console
- Check email settings if using email alerts

### Database Errors
- Run migrations: `flask db upgrade`
- Check DATABASE_URL in .env
- Verify database is running

### High CPU Usage
- Reduce FRAME_SKIP in config
- Lower camera resolution
- Disable unused detection types

## Performance Optimization

- Frame processing: Every 2 seconds (adjustable)
- Detection confidence: 50% (adjustable)
- WebSocket: Automatic reconnection
- Redis caching: Session and temporary data

## Deployment Checklist

- [ ] Update SECRET_KEY and JWT_SECRET_KEY
- [ ] Configure production database
- [ ] Set FLASK_ENV=production
- [ ] Enable HTTPS
- [ ] Configure email server
- [ ] Setup Redis
- [ ] Run database migrations
- [ ] Test camera access
- [ ] Configure firewall
- [ ] Setup monitoring

## License

MIT License

## Support

For issues, create a GitHub issue or contact support.

## Roadmap

- [ ] Mobile app (React Native)
- [ ] YOLO v8 integration
- [ ] Cloud storage
- [ ] Multi-camera sync
- [ ] Advanced ML models
- [ ] Voice control
- [ ] Facial recognition
- [ ] License plate detection
