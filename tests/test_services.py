import pytest
from unittest.mock import MagicMock, patch
from app.services.firebase_service import FirebaseService
from app.services.notification_service import NotificationService
from app.services.door_control_service import DoorControlService
from app.models import DeviceToken, User, db

@pytest.fixture
def mock_firebase_admin():
    with patch('firebase_admin.initialize_app'), \
         patch('firebase_admin.credentials.Certificate'), \
         patch('firebase_admin.db.reference') as mock_db, \
         patch('firebase_admin.storage.bucket') as mock_storage, \
         patch('firebase_admin.messaging.send_multicast') as mock_messaging, \
         patch('firebase_admin.messaging.Notification'), \
         patch('firebase_admin.messaging.AndroidConfig'), \
         patch('firebase_admin.messaging.APNSConfig'), \
         patch('firebase_admin.messaging.MulticastMessage'):
        yield {
            'db': mock_db,
            'storage': mock_storage,
            'messaging': mock_messaging
        }

class TestFirebaseService:
    def test_init_disabled(self, app):
        """Test initializing service when disabled in config"""
        app.config['FIREBASE_ENABLED'] = False
        service = FirebaseService()
        assert not service.is_enabled

    def test_log_entry(self, app, mock_firebase_admin):
        """Test logging entry to Firebase"""
        app.config['FIREBASE_ENABLED'] = True
        service = FirebaseService()
        
        entry_data = {
            'person_name': 'John Doe',
            'camera_id': 'cam_1',
            'is_known': True
        }
        
        entry_id = service.log_entry(entry_data)
        assert entry_id is not None
        assert entry_id.startswith('entry_')
        mock_firebase_admin['db'].return_value.child.return_value.child.return_value.set.assert_called_once()

    def test_upload_image(self, app, mock_firebase_admin):
        """Test uploading image to Firebase Storage"""
        app.config['FIREBASE_ENABLED'] = True
        service = FirebaseService()
        
        # Mock file existence and blob
        with patch('os.path.exists', return_value=True):
            mock_blob = MagicMock()
            mock_blob.public_url = 'https://storage.googleapis.com/test.jpg'
            mock_firebase_admin['storage'].return_value.blob.return_value = mock_blob
            
            url = service.upload_image('/tmp/test.jpg', 'entries/test.jpg')
            
            assert url == 'https://storage.googleapis.com/test.jpg'
            mock_blob.upload_from_filename.assert_called_with('/tmp/test.jpg')
            mock_blob.make_public.assert_called_once()


class TestNotificationService:
    @patch('app.services.notification_service.NotificationService._get_admin_tokens')
    def test_send_entry_alert(self, mock_get_tokens, app, mock_firebase_admin):
        """Test sending entry alert notification"""
        app.config['ENABLE_PUSH_NOTIFICATIONS'] = True
        mock_get_tokens.return_value = ['token1', 'token2']
        
        service = NotificationService()
        service.firebase._enabled = True  # Force enable helper
        
        entry_data = {
            'person_name': 'Stranger',
            'camera_id': 'Front Door',
            'is_known': False,
            'image_url': 'http://example.com/image.jpg'
        }
        
        response = service.send_entry_alert(entry_data)
        
        # Verify messaging called
        mock_firebase_admin['messaging'].assert_called_once()
        args = mock_firebase_admin['messaging'].call_args
        # You'd check args detailed here if needed

    def test_quiet_hours(self, app):
        """Test quiet hours logic"""
        service = NotificationService()
        
        # Mock time to 3 AM
        with patch('app.services.notification_service.datetime') as mock_dt:
            mock_dt.now.return_value.hour = 3
            mock_dt.now.return_value.minute = 0
            
            # Quiet hours 22:00-07:00
            app.config['NOTIFICATION_QUIET_HOURS'] = '22:00-07:00'
            assert service._is_quiet_hours() is True
            
            # Mock time to 2 PM
            mock_dt.now.return_value.hour = 14
            assert service._is_quiet_hours() is False


class TestDoorControlService:
    def test_auto_open_resident(self, app):
        """Test auto-opening door for residents"""
        app.config['AUTO_OPEN_RESIDENTS'] = True
        service = DoorControlService(protocol='mock')
        
        result = service.process_recognition({
            'is_known': True,
            'is_resident': True,
            'person_name': 'Resident',
            'confidence': 0.95
        }, camera_id=1)
        
        assert result['action'] == 'door_opened'
        assert result['access_granted'] is True
        assert result['door_status'] == 'unlocked'

    def test_guest_approval_required(self, app):
        """Test guest requires approval"""
        app.config['REQUIRE_APPROVAL_FOR_GUESTS'] = True
        service = DoorControlService(protocol='mock')
        
        result = service.process_recognition({
            'is_known': True,
            'is_resident': False,
            'person_name': 'Guest',
            'relation': 'guest',
            'confidence': 0.90
        }, camera_id=1)
        
        assert result['action'] == 'pending_approval'
        assert result['access_granted'] is False

    def test_unknown_person_denied(self, app):
        """Test unknown person is alerted but not opened"""
        service = DoorControlService(protocol='mock')
        
        result = service.process_recognition({
            'is_known': False,
            'person_name': 'Unknown',
            'confidence': 0.0
        }, camera_id=1)
        
        assert result['action'] == 'alert_sent'
        assert result['access_granted'] is False
