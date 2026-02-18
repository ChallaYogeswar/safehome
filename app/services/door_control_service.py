"""
Door Control Service
Handles smart lock integration for automated access control
Supports multiple lock types: WiFi, Z-Wave, HTTP API
"""

from flask import current_app
from datetime import datetime, timezone
import logging
import requests
import time

logger = logging.getLogger(__name__)


class DoorControlService:
    """Handle smart lock operations and door access control"""
    
    # Supported lock protocols
    PROTOCOL_HTTP = 'http'
    PROTOCOL_WIFI = 'wifi'
    PROTOCOL_ZWAVE = 'zwave'
    PROTOCOL_MOCK = 'mock'  # For testing without hardware
    
    def __init__(self, protocol=None):
        self.protocol = protocol or current_app.config.get('DOOR_LOCK_PROTOCOL', 'mock')
        self.auto_open_residents = current_app.config.get('AUTO_OPEN_RESIDENTS', True)
        self.auto_open_duration = current_app.config.get('AUTO_OPEN_DURATION', 5)
        self.require_approval = current_app.config.get('REQUIRE_APPROVAL_FOR_GUESTS', True)
        
        # Lock state tracking
        self._lock_states = {}
    
    def process_recognition(self, recognition_result, camera_id, image_path=None):
        """
        Process a face recognition result and determine door action
        
        Args:
            recognition_result: Recognition dict from FaceRecognitionService
            camera_id: ID of the camera that detected the face
            image_path: Path to the captured image
        
        Returns:
            {
                'action': str ('door_opened', 'pending_approval', 'entry_denied'),
                'access_granted': bool,
                'message': str,
                'door_status': str
            }
        """
        is_known = recognition_result.get('is_known', False)
        is_resident = recognition_result.get('is_resident', False)
        person_name = recognition_result.get('person_name', 'Unknown')
        confidence = recognition_result.get('confidence', 0.0)
        
        # Decision logic
        if is_known and is_resident and self.auto_open_residents:
            # Known resident — auto-open door
            success = self.unlock_door(camera_id)
            action = 'door_opened' if success else 'alert_sent'
            return {
                'action': action,
                'access_granted': success,
                'message': f'Door opened for {person_name}' if success else f'Door unlock failed for {person_name}',
                'door_status': 'unlocked' if success else 'locked'
            }
        
        elif is_known and not is_resident:
            # Known but not resident (guest/staff)
            if self.require_approval:
                return {
                    'action': 'pending_approval',
                    'access_granted': False,
                    'message': f'Approval required for {person_name} ({recognition_result.get("relation", "guest")})',
                    'door_status': 'locked'
                }
            else:
                success = self.unlock_door(camera_id)
                action = 'door_opened' if success else 'alert_sent'
                return {
                    'action': action,
                    'access_granted': success,
                    'message': f'Door opened for guest {person_name}',
                    'door_status': 'unlocked' if success else 'locked'
                }
        
        else:
            # Unknown person — deny and alert
            return {
                'action': 'alert_sent',
                'access_granted': False,
                'message': f'Unknown person detected — alert sent',
                'door_status': 'locked'
            }
    
    def unlock_door(self, camera_id, duration=None):
        """
        Unlock the door associated with a camera
        
        Args:
            camera_id: Camera/door identifier
            duration: Seconds to keep unlocked (default: AUTO_OPEN_DURATION)
        
        Returns:
            bool: Success status
        """
        duration = duration or self.auto_open_duration
        
        try:
            if self.protocol == self.PROTOCOL_MOCK:
                return self._mock_unlock(camera_id, duration)
            elif self.protocol == self.PROTOCOL_HTTP:
                return self._http_unlock(camera_id, duration)
            elif self.protocol == self.PROTOCOL_WIFI:
                return self._wifi_unlock(camera_id, duration)
            elif self.protocol == self.PROTOCOL_ZWAVE:
                return self._zwave_unlock(camera_id, duration)
            else:
                logger.error(f"Unknown lock protocol: {self.protocol}")
                return False
                
        except Exception as e:
            logger.error(f"Error unlocking door for camera {camera_id}: {e}")
            return False
    
    def lock_door(self, camera_id):
        """
        Lock the door associated with a camera
        
        Args:
            camera_id: Camera/door identifier
        
        Returns:
            bool: Success status
        """
        try:
            if self.protocol == self.PROTOCOL_MOCK:
                return self._mock_lock(camera_id)
            elif self.protocol == self.PROTOCOL_HTTP:
                return self._http_lock(camera_id)
            elif self.protocol == self.PROTOCOL_WIFI:
                return self._wifi_lock(camera_id)
            elif self.protocol == self.PROTOCOL_ZWAVE:
                return self._zwave_lock(camera_id)
            else:
                logger.error(f"Unknown lock protocol: {self.protocol}")
                return False
                
        except Exception as e:
            logger.error(f"Error locking door for camera {camera_id}: {e}")
            return False
    
    def get_door_status(self, camera_id):
        """
        Get the current status of a door
        
        Returns:
            {
                'camera_id': int,
                'status': str ('locked', 'unlocked', 'unknown'),
                'last_action': str,
                'last_action_time': str
            }
        """
        state = self._lock_states.get(str(camera_id), {})
        return {
            'camera_id': camera_id,
            'status': state.get('status', 'unknown'),
            'last_action': state.get('last_action', 'none'),
            'last_action_time': state.get('last_action_time', None)
        }
    
    def approve_entry(self, camera_id, approved_by):
        """
        Approve a pending entry — unlock the door
        
        Args:
            camera_id: Camera/door identifier
            approved_by: Username who approved
        
        Returns:
            bool: Success status
        """
        logger.info(f"Entry approved by {approved_by} for camera {camera_id}")
        success = self.unlock_door(camera_id)
        
        if success:
            self._update_lock_state(camera_id, 'unlocked', f'approved_by_{approved_by}')
        
        return success
    
    def deny_entry(self, camera_id, denied_by):
        """
        Deny a pending entry — keep door locked
        
        Args:
            camera_id: Camera/door identifier
            denied_by: Username who denied
        
        Returns:
            bool: Always True (door stays locked)
        """
        logger.info(f"Entry denied by {denied_by} for camera {camera_id}")
        self._update_lock_state(camera_id, 'locked', f'denied_by_{denied_by}')
        return True
    
    # ── Protocol Implementations ──────────────────────────────────────
    
    def _mock_unlock(self, camera_id, duration):
        """Mock unlock for development/testing"""
        logger.info(f"🔓 [MOCK] Door unlocked for camera {camera_id} ({duration}s)")
        self._update_lock_state(camera_id, 'unlocked', 'mock_unlock')
        return True
    
    def _mock_lock(self, camera_id):
        """Mock lock for development/testing"""
        logger.info(f"🔒 [MOCK] Door locked for camera {camera_id}")
        self._update_lock_state(camera_id, 'locked', 'mock_lock')
        return True
    
    def _http_unlock(self, camera_id, duration):
        """
        Unlock via HTTP API (for smart locks with REST endpoints)
        Example: August, Yale Connect, or custom ESP32/Arduino locks
        """
        lock_url = current_app.config.get('DOOR_LOCK_HTTP_URL')
        lock_api_key = current_app.config.get('DOOR_LOCK_API_KEY')
        
        if not lock_url:
            logger.error("DOOR_LOCK_HTTP_URL not configured")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {lock_api_key}'} if lock_api_key else {}
            response = requests.post(
                f"{lock_url}/unlock",
                json={'camera_id': camera_id, 'duration': duration},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self._update_lock_state(camera_id, 'unlocked', 'http_unlock')
                logger.info(f"🔓 Door unlocked via HTTP for camera {camera_id}")
                return True
            else:
                logger.error(f"HTTP unlock failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"HTTP unlock timeout for camera {camera_id}")
            return False
        except Exception as e:
            logger.error(f"HTTP unlock error: {e}")
            return False
    
    def _http_lock(self, camera_id):
        """Lock via HTTP API"""
        lock_url = current_app.config.get('DOOR_LOCK_HTTP_URL')
        lock_api_key = current_app.config.get('DOOR_LOCK_API_KEY')
        
        if not lock_url:
            return False
        
        try:
            headers = {'Authorization': f'Bearer {lock_api_key}'} if lock_api_key else {}
            response = requests.post(
                f"{lock_url}/lock",
                json={'camera_id': camera_id},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self._update_lock_state(camera_id, 'locked', 'http_lock')
                return True
            return False
            
        except Exception as e:
            logger.error(f"HTTP lock error: {e}")
            return False
    
    def _wifi_unlock(self, camera_id, duration):
        """WiFi-based smart lock unlock (placeholder for vendor SDK)"""
        logger.warning("WiFi lock protocol not fully implemented — using mock")
        return self._mock_unlock(camera_id, duration)
    
    def _wifi_lock(self, camera_id):
        """WiFi-based smart lock lock (placeholder for vendor SDK)"""
        logger.warning("WiFi lock protocol not fully implemented — using mock")
        return self._mock_lock(camera_id)
    
    def _zwave_unlock(self, camera_id, duration):
        """Z-Wave smart lock unlock (placeholder for Z-Wave integration)"""
        logger.warning("Z-Wave lock protocol not fully implemented — using mock")
        return self._mock_unlock(camera_id, duration)
    
    def _zwave_lock(self, camera_id):
        """Z-Wave smart lock lock (placeholder for Z-Wave integration)"""
        logger.warning("Z-Wave lock protocol not fully implemented — using mock")
        return self._mock_lock(camera_id)
    
    # ── Internal Helpers ──────────────────────────────────────────────
    
    def _update_lock_state(self, camera_id, status, action):
        """Update internal lock state tracking"""
        self._lock_states[str(camera_id)] = {
            'status': status,
            'last_action': action,
            'last_action_time': datetime.now(timezone.utc).isoformat()
        }
