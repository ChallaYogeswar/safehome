"""
Firebase Service
Handles all Firebase operations: Realtime Database, Cloud Storage, and Cloud Messaging
"""

from flask import current_app
from datetime import datetime, timezone
import uuid
import logging
import os

logger = logging.getLogger(__name__)


class FirebaseService:
    """Handle all Firebase operations with graceful fallback"""
    
    def __init__(self):
        self._enabled = current_app.config.get('FIREBASE_ENABLED', False)
        self._db_ref = None
        self._bucket = None
        
        if self._enabled:
            try:
                from firebase_admin import db as firebase_db, storage
                self._db_ref = firebase_db.reference()
                self._bucket = storage.bucket()
            except Exception as e:
                logger.error(f"Firebase service init error: {e}")
                self._enabled = False
    
    @property
    def is_enabled(self):
        return self._enabled
    
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
            firebase_entry_id: str or None
        """
        if not self._enabled:
            logger.warning("Firebase not enabled — skipping entry log")
            return None
        
        try:
            entry_id = f"entry_{uuid.uuid4().hex[:12]}"
            
            self._db_ref.child('entries').child(entry_id).set({
                'person_id': entry_data.get('person_id'),
                'person_name': entry_data.get('person_name', 'Unknown'),
                'camera_id': entry_data.get('camera_id'),
                'is_known': entry_data.get('is_known', False),
                'confidence': entry_data.get('confidence', 0.0),
                'action': entry_data.get('action', 'pending'),
                'timestamp': entry_data.get('timestamp', int(datetime.now(timezone.utc).timestamp() * 1000)),
                'image_url': entry_data.get('image_url'),
                'approved_by': entry_data.get('approved_by')
            })
            
            logger.info(f"✅ Logged entry {entry_id} to Firebase")
            return entry_id
            
        except Exception as e:
            logger.error(f"Error logging entry to Firebase: {e}")
            return None
    
    def upload_image(self, image_path, destination_path):
        """
        Upload image to Firebase Storage
        
        Args:
            image_path: Local file path
            destination_path: Path in Firebase Storage (e.g., 'entries/entry_001.jpg')
        
        Returns:
            public_url: str or None
        """
        if not self._enabled:
            logger.warning("Firebase not enabled — skipping image upload")
            return None
        
        try:
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return None
            
            blob = self._bucket.blob(destination_path)
            blob.upload_from_filename(image_path)
            blob.make_public()
            
            public_url = blob.public_url
            logger.info(f"✅ Uploaded image to Firebase: {destination_path}")
            return public_url
            
        except Exception as e:
            logger.error(f"Error uploading image to Firebase: {e}")
            return None
    
    def send_push_notification(self, device_tokens, notification_data):
        """
        Send push notification via Firebase Cloud Messaging (FCM)
        
        Args:
            device_tokens: List of device token strings
            notification_data: {
                'title': str,
                'body': str,
                'image_url': str (optional),
                'data': dict (custom data, optional)
            }
        
        Returns:
            response: FCM response object or None
        """
        if not self._enabled:
            logger.warning("Firebase not enabled — skipping push notification")
            return None
        
        if not device_tokens:
            logger.warning("No device tokens provided — skipping notification")
            return None
        
        try:
            from firebase_admin import messaging
            
            # Prepare notification
            notification = messaging.Notification(
                title=notification_data.get('title', 'SafeHome Alert'),
                body=notification_data.get('body', ''),
                image=notification_data.get('image_url')
            )
            
            # Prepare data payload (all values must be strings)
            data = notification_data.get('data', {})
            str_data = {k: str(v) for k, v in data.items()}
            
            # Android-specific config
            android_config = messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound='alert',
                    channel_id='safehome_alerts',
                    priority='high'
                )
            )
            
            # iOS-specific config
            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='alert.wav',
                        badge=1
                    )
                )
            )
            
            # Send multicast message
            message = messaging.MulticastMessage(
                tokens=device_tokens,
                notification=notification,
                data=str_data,
                android=android_config,
                apns=apns_config
            )
            
            response = messaging.send_multicast(message)
            logger.info(
                f"✅ Push notification sent: {response.success_count} success, "
                f"{response.failure_count} failures"
            )
            
            # Handle failed tokens
            if response.failure_count > 0:
                self._handle_failed_tokens(device_tokens, response.responses)
            
            return response
            
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return None
    
    def _handle_failed_tokens(self, tokens, responses):
        """Remove invalid/expired device tokens from database"""
        from firebase_admin import messaging
        from app.models import DeviceToken, db
        
        for idx, resp in enumerate(responses):
            if resp.exception:
                error_code = getattr(resp.exception, 'code', '')
                if error_code in ['NOT_FOUND', 'INVALID_ARGUMENT', 'UNREGISTERED']:
                    try:
                        token_record = DeviceToken.query.filter_by(token=tokens[idx]).first()
                        if token_record:
                            token_record.is_active = False
                            db.session.commit()
                            logger.info(f"Deactivated invalid token: {tokens[idx][:20]}...")
                    except Exception as e:
                        logger.error(f"Error deactivating token: {e}")
    
    def sync_person(self, person_data):
        """
        Sync enrolled person to Firebase Realtime Database
        
        Args:
            person_data: {
                'id': str,
                'name': str,
                'relation': str,
                'is_resident': bool,
                'enrolled_date': int (epoch ms),
                'encoding_count': int
            }
        
        Returns:
            firebase_person_id: str or None
        """
        if not self._enabled:
            logger.warning("Firebase not enabled — skipping person sync")
            return None
        
        try:
            person_id = str(person_data['id'])
            
            self._db_ref.child('persons').child(person_id).set({
                'name': person_data.get('name'),
                'relation': person_data.get('relation', 'family'),
                'is_resident': person_data.get('is_resident', True),
                'enrolled_date': person_data.get('enrolled_date'),
                'encoding_count': person_data.get('encoding_count', 0),
                'last_seen': None
            })
            
            logger.info(f"✅ Synced person '{person_data.get('name')}' to Firebase")
            return person_id
            
        except Exception as e:
            logger.error(f"Error syncing person to Firebase: {e}")
            return None
    
    def update_entry_action(self, firebase_entry_id, action, approved_by=None):
        """
        Update an entry's action in Firebase (e.g., approve/deny)
        
        Args:
            firebase_entry_id: Firebase entry ID
            action: New action ('door_opened', 'entry_denied', etc.)
            approved_by: Username who approved/denied
        
        Returns:
            bool: Success status
        """
        if not self._enabled or not firebase_entry_id:
            return False
        
        try:
            updates = {
                'action': action,
                'approved_by': approved_by,
                'updated_at': int(datetime.now(timezone.utc).timestamp() * 1000)
            }
            
            self._db_ref.child('entries').child(firebase_entry_id).update(updates)
            logger.info(f"✅ Updated entry {firebase_entry_id} action to '{action}'")
            return True
            
        except Exception as e:
            logger.error(f"Error updating entry in Firebase: {e}")
            return False
    
    def delete_person(self, person_id):
        """Remove a person from Firebase"""
        if not self._enabled:
            return False
        
        try:
            self._db_ref.child('persons').child(str(person_id)).delete()
            logger.info(f"✅ Deleted person {person_id} from Firebase")
            return True
        except Exception as e:
            logger.error(f"Error deleting person from Firebase: {e}")
            return False
