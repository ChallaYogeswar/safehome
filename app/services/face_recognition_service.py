"""
Face Recognition Service
Handles face detection, encoding, and matching for access control
"""

import face_recognition
import numpy as np
import cv2
from PIL import Image
import io
import os
from datetime import datetime, timezone
from app.models import FacePerson, FaceEncoding, AccessLog, db

class FaceRecognitionService:
    """Service for face detection and recognition"""
    
    # Face matching tolerance (lower = stricter matching)
    FACE_MATCH_TOLERANCE = 0.6
    
    # Minimum faces needed to train a person
    MIN_ENCODING_COUNT = 2
    
    def __init__(self):
        self.face_detector = face_recognition.load_image_file
        self.face_encodings_model = face_recognition.face_encodings
    
    @staticmethod
    def encode_image_file(image_path: str) -> list:
        """
        Load image and extract face encodings
        Returns list of (encoding, face_location) tuples
        """
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image, model='hog')
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            return [
                {
                    'encoding': encoding.tolist(),
                    'location': location,
                    'confidence': 0.95  # Face_recognition doesn't return confidence
                }
                for encoding, location in zip(face_encodings, face_locations)
            ]
        except Exception as e:
            print(f"Error encoding image {image_path}: {str(e)}")
            return []
    
    @staticmethod
    def encode_opencv_frame(frame) -> list:
        """
        Extract faces from OpenCV frame (numpy array)
        Returns list of encodings with locations
        """
        try:
            # OpenCV uses BGR, face_recognition uses RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            face_locations = face_recognition.face_locations(rgb_frame, model='hog')
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            return [
                {
                    'encoding': encoding.tolist(),
                    'location': location,
                }
                for encoding, location in zip(face_encodings, face_locations)
            ]
        except Exception as e:
            print(f"Error encoding frame: {str(e)}")
            return []
    
    @staticmethod
    def encode_pil_image(pil_image) -> list:
        """
        Extract faces from PIL Image
        Returns list of encodings with locations
        """
        try:
            # Convert PIL image to numpy array
            image_array = np.array(pil_image)
            
            # If grayscale, convert to RGB
            if len(image_array.shape) == 2:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
            elif image_array.shape[2] == 4:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2RGB)
            
            face_locations = face_recognition.face_locations(image_array, model='hog')
            face_encodings = face_recognition.face_encodings(image_array, face_locations)
            
            return [
                {
                    'encoding': encoding.tolist(),
                    'location': location,
                }
                for encoding, location in zip(face_encodings, face_locations)
            ]
        except Exception as e:
            print(f"Error encoding PIL image: {str(e)}")
            return []
    
    @staticmethod
    def compare_faces(test_encoding: list, known_encodings: list, tolerance: float = None) -> list:
        """
        Compare a test encoding against multiple known encodings
        Returns list of boolean matches
        """
        if tolerance is None:
            tolerance = FaceRecognitionService.FACE_MATCH_TOLERANCE
        
        test_encoding = np.array(test_encoding)
        known_encodings = np.array(known_encodings)
        
        distances = face_recognition.face_distance(known_encodings, test_encoding)
        return (distances <= tolerance).tolist()
    
    @staticmethod
    def find_closest_match(test_encoding: list, known_encodings: list) -> dict:
        """
        Find the closest matching encoding
        Returns {'match_index': int, 'distance': float, 'confidence': float}
        """
        test_encoding = np.array(test_encoding)
        known_encodings = np.array(known_encodings)
        
        distances = face_recognition.face_distance(known_encodings, test_encoding)
        
        if len(distances) == 0:
            return {'match_index': -1, 'distance': 1.0, 'confidence': 0.0}
        
        match_index = int(np.argmin(distances))
        distance = float(distances[match_index])
        confidence = 1.0 - distance  # Convert distance to confidence (0-1)
        
        return {
            'match_index': match_index,
            'distance': distance,
            'confidence': confidence,
            'is_match': distance <= FaceRecognitionService.FACE_MATCH_TOLERANCE
        }
    
    @staticmethod
    def enroll_person(user_id: int, person_name: str, image_paths: list, 
                     relation: str = 'family', is_resident: bool = True) -> dict:
        """
        Enroll a new person with multiple face images
        Returns {'success': bool, 'message': str, 'person_id': int}
        """
        try:
            # Create FacePerson entry
            face_person = FacePerson(
                user_id=user_id,
                name=person_name,
                relation=relation,
                is_resident=is_resident,
                profile_image=image_paths[0] if image_paths else None
            )
            db.session.add(face_person)
            db.session.flush()
            
            # Encode all images and store encodings
            encoding_count = 0
            for image_path in image_paths:
                encodings_data = FaceRecognitionService.encode_image_file(image_path)
                
                for enc_data in encodings_data:
                    face_encoding = FaceEncoding(
                        person_id=face_person.id,
                        encoding=enc_data['encoding'],
                        image_path=image_path
                    )
                    db.session.add(face_encoding)
                    encoding_count += 1
            
            if encoding_count < FaceRecognitionService.MIN_ENCODING_COUNT:
                db.session.rollback()
                return {
                    'success': False,
                    'message': f'Need at least {FaceRecognitionService.MIN_ENCODING_COUNT} faces, got {encoding_count}'
                }
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Successfully enrolled {person_name} with {encoding_count} face encodings',
                'person_id': face_person.id,
                'encoding_count': encoding_count
            }
        
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Error enrolling person: {str(e)}'}
    
    @staticmethod
    def recognize_face(camera_id: int, test_encoding: list) -> dict:
        """
        Recognize a face against all enrolled persons for the camera's user
        Returns {'is_known': bool, 'person_id': int, 'person_name': str, 
                 'confidence': float, 'match_details': dict}
        """
        from app.models import Camera, User
        
        try:
            # Get camera and user
            camera = Camera.query.get(camera_id)
            if not camera:
                return {'is_known': False, 'error': 'Camera not found'}
            
            user = User.query.get(camera.user_id)
            if not user:
                return {'is_known': False, 'error': 'User not found'}
            
            # Get all face persons for this user
            face_persons = FacePerson.query.filter_by(user_id=user.id).all()
            
            if not face_persons:
                return {
                    'is_known': False,
                    'message': 'No enrolled persons for this camera',
                    'confidence': 0.0
                }
            
            best_match = None
            best_distance = float('inf')
            
            # Compare against all enrolled persons
            for person in face_persons:
                encodings = FaceEncoding.query.filter_by(person_id=person.id).all()
                
                if not encodings:
                    continue
                
                known_encodings = [enc.encoding for enc in encodings]
                match_result = FaceRecognitionService.find_closest_match(
                    test_encoding, known_encodings
                )
                
                if match_result['is_match'] and match_result['distance'] < best_distance:
                    best_match = person
                    best_distance = match_result['distance']
            
            if best_match:
                return {
                    'is_known': True,
                    'person_id': best_match.id,
                    'person_name': best_match.name,
                    'confidence': 1.0 - best_distance,
                    'relation': best_match.relation,
                    'is_resident': best_match.is_resident
                }
            else:
                return {
                    'is_known': False,
                    'confidence': 0.0,
                    'message': 'Face does not match any enrolled person'
                }
        
        except Exception as e:
            return {'is_known': False, 'error': f'Recognition error: {str(e)}'}
    
    @staticmethod
    def log_access(camera_id: int, test_encoding: list, image_path: str = None,
                   manual_person_name: str = None) -> dict:
        """
        Log an access attempt and determine if access should be granted
        Returns {'access_granted': bool, 'action': str, 'person_info': dict}
        """
        from app.models import Camera
        
        try:
            camera = Camera.query.get(camera_id)
            if not camera:
                return {'access_granted': False, 'error': 'Camera not found'}
            
            if not camera.access_control_enabled:
                return {'access_granted': False, 'message': 'Access control not enabled'}
            
            # Recognize the face
            recognition_result = FaceRecognitionService.recognize_face(camera_id, test_encoding)
            
            # Determine access and action
            access_granted = False
            action = 'alert_sent'
            person_id = None
            person_name = manual_person_name or 'Unknown'
            is_known = recognition_result.get('is_known', False)
            confidence = recognition_result.get('confidence', 0.0)
            
            if is_known and recognition_result.get('is_resident'):
                access_granted = True
                action = 'door_opened'
                person_id = recognition_result.get('person_id')
                person_name = recognition_result.get('person_name')
            elif is_known:
                # Known but not resident (guest/staff)
                action = 'alert_sent'
                person_id = recognition_result.get('person_id')
                person_name = recognition_result.get('person_name')
            else:
                # Unknown person - alert
                action = 'alert_sent'
            
            # Log the access attempt
            access_log = AccessLog(
                camera_id=camera_id,
                person_id=person_id,
                person_name=person_name,
                is_known=is_known,
                confidence=confidence,
                image_path=image_path,
                access_granted=access_granted,
                action=action
            )
            db.session.add(access_log)
            db.session.commit()
            
            return {
                'access_granted': access_granted,
                'action': action,
                'person_info': {
                    'name': person_name,
                    'is_known': is_known,
                    'confidence': confidence,
                    'relation': recognition_result.get('relation', 'unknown')
                }
            }
        
        except Exception as e:
            return {'access_granted': False, 'error': f'Error logging access: {str(e)}'}
    
    @staticmethod
    def get_enrolled_persons(user_id: int) -> list:
        """Get all enrolled persons for a user"""
        persons = FacePerson.query.filter_by(user_id=user_id).all()
        return [
            {
                'id': p.id,
                'name': p.name,
                'relation': p.relation,
                'is_resident': p.is_resident,
                'profile_image': p.profile_image,
                'encoding_count': p.face_encodings.count(),
                'recognition_count': p.recognition_count,
                'last_recognized': p.last_recognized.isoformat() if p.last_recognized else None
            }
            for p in persons
        ]
    
    @staticmethod
    def delete_enrolled_person(person_id: int, user_id: int) -> dict:
        """Delete an enrolled person and all their encodings"""
        try:
            person = FacePerson.query.filter_by(id=person_id, user_id=user_id).first()
            if not person:
                return {'success': False, 'message': 'Person not found'}
            
            db.session.delete(person)
            db.session.commit()
            
            return {'success': True, 'message': f'Deleted {person.name} from enrollment'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Error deleting person: {str(e)}'}
