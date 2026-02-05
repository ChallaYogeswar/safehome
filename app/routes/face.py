"""
Face Recognition & Access Control Routes
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timezone
from PIL import Image
import io

from app.models import Camera, FacePerson, FaceEncoding, AccessLog, db
from app.services.face_recognition_service import FaceRecognitionService

bp = Blueprint('face', __name__, url_prefix='/face')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'uploads/faces'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.before_request
def ensure_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

@bp.route('/enroll', methods=['POST'])
@login_required
def enroll_person():
    """
    Enroll a new person with multiple face photos
    POST /face/enroll
    
    Form data:
    - person_name: str (required)
    - relation: str (optional: 'family', 'guest', 'staff')
    - is_resident: bool (optional, default: true)
    - images: file[] (multiple image files)
    """
    try:
        person_name = request.form.get('person_name')
        relation = request.form.get('relation', 'family')
        is_resident = request.form.get('is_resident', 'true').lower() == 'true'
        
        if not person_name:
            return jsonify({'success': False, 'message': 'Person name required'}), 400
        
        if 'images' not in request.files:
            return jsonify({'success': False, 'message': 'No images provided'}), 400
        
        files = request.files.getlist('images')
        if not files or len(files) == 0:
            return jsonify({'success': False, 'message': 'No images provided'}), 400
        
        # Save uploaded images
        saved_paths = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{current_user.id}_{person_name}_{datetime.now(timezone.utc).timestamp()}_{file.filename}")
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                saved_paths.append(filepath)
        
        if not saved_paths:
            return jsonify({'success': False, 'message': 'No valid images provided'}), 400
        
        # Enroll person
        result = FaceRecognitionService.enroll_person(
            current_user.id,
            person_name,
            saved_paths,
            relation=relation,
            is_resident=is_resident
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            # Clean up files if enrollment failed
            for path in saved_paths:
                if os.path.exists(path):
                    os.remove(path)
            return jsonify(result), 400
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@bp.route('/enrolled', methods=['GET'])
@login_required
def list_enrolled_persons():
    """Get all enrolled persons for current user"""
    try:
        persons = FaceRecognitionService.get_enrolled_persons(current_user.id)
        return jsonify({'success': True, 'persons': persons}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@bp.route('/enrolled/<int:person_id>', methods=['DELETE'])
@login_required
def delete_enrolled_person(person_id):
    """Delete an enrolled person"""
    try:
        result = FaceRecognitionService.delete_enrolled_person(person_id, current_user.id)
        status = 200 if result['success'] else 404
        return jsonify(result), status
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@bp.route('/recognize', methods=['POST'])
@login_required
def recognize():
    """
    Recognize a face from uploaded image or camera frame
    POST /face/recognize
    
    JSON:
    - camera_id: int (required)
    - image_data: str (base64 image, required) OR
    - image_file: file (image file)
    """
    try:
        camera_id = request.form.get('camera_id') or request.json.get('camera_id')
        
        if not camera_id:
            return jsonify({'success': False, 'message': 'camera_id required'}), 400
        
        camera_id = int(camera_id)
        
        # Verify camera belongs to user
        camera = Camera.query.filter_by(id=camera_id, user_id=current_user.id).first()
        if not camera:
            return jsonify({'success': False, 'message': 'Camera not found'}), 404
        
        # Get image
        image_data = None
        image_path = None
        
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"recognition_{datetime.now(timezone.utc).timestamp()}_{file.filename}")
                image_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(image_path)
        elif 'image_data' in request.form:
            import base64
            image_data = request.form['image_data']
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            try:
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
                filename = f"recognition_{datetime.now(timezone.utc).timestamp()}.jpg"
                image_path = os.path.join(UPLOAD_FOLDER, filename)
                image.save(image_path)
            except Exception as e:
                return jsonify({'success': False, 'message': f'Invalid image data: {str(e)}'}), 400
        else:
            return jsonify({'success': False, 'message': 'No image provided'}), 400
        
        # Extract face encoding
        encodings_data = FaceRecognitionService.encode_image_file(image_path)
        
        if not encodings_data:
            return jsonify({
                'success': False,
                'message': 'No face detected in image'
            }), 400
        
        # Use first face detected
        test_encoding = encodings_data[0]['encoding']
        
        # Recognize face
        recognition_result = FaceRecognitionService.recognize_face(camera_id, test_encoding)
        
        return jsonify({
            'success': True,
            'recognition': recognition_result,
            'image_path': image_path
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@bp.route('/access-log', methods=['GET'])
@login_required
def access_log():
    """
    Get access logs for user's cameras
    Query params:
    - camera_id: int (optional)
    - limit: int (default: 50)
    - offset: int (default: 0)
    """
    try:
        camera_id = request.args.get('camera_id', type=int)
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        query = db.session.query(AccessLog).join(Camera).filter(
            Camera.user_id == current_user.id
        )
        
        if camera_id:
            query = query.filter(AccessLog.camera_id == camera_id)
        
        total = query.count()
        logs = query.order_by(AccessLog.timestamp.desc()).offset(offset).limit(limit).all()
        
        logs_data = [
            {
                'id': log.id,
                'camera_id': log.camera_id,
                'person_name': log.person_name,
                'is_known': log.is_known,
                'confidence': log.confidence,
                'access_granted': log.access_granted,
                'action': log.action,
                'timestamp': log.timestamp.isoformat(),
                'image_path': log.image_path
            }
            for log in logs
        ]
        
        return jsonify({
            'success': True,
            'total': total,
            'logs': logs_data
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@bp.route('/camera/<int:camera_id>/enable-access-control', methods=['POST'])
@login_required
def enable_access_control(camera_id):
    """Enable access control on a camera"""
    try:
        camera = Camera.query.filter_by(id=camera_id, user_id=current_user.id).first()
        if not camera:
            return jsonify({'success': False, 'message': 'Camera not found'}), 404
        
        camera.access_control_enabled = True
        camera.face_detection_enabled = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Access control enabled',
            'camera': {
                'id': camera.id,
                'name': camera.name,
                'access_control_enabled': camera.access_control_enabled,
                'face_detection_enabled': camera.face_detection_enabled
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@bp.route('/stats', methods=['GET'])
@login_required
def stats():
    """Get face recognition statistics"""
    try:
        enrolled_count = FacePerson.query.filter_by(user_id=current_user.id).count()
        total_encodings = db.session.query(FaceEncoding).join(FacePerson).filter(
            FacePerson.user_id == current_user.id
        ).count()
        
        recent_access = db.session.query(AccessLog).join(Camera).filter(
            Camera.user_id == current_user.id
        ).order_by(AccessLog.timestamp.desc()).limit(10).all()
        
        access_granted = db.session.query(AccessLog).join(Camera).filter(
            Camera.user_id == current_user.id,
            AccessLog.access_granted == True
        ).count()
        
        unknown_persons = db.session.query(AccessLog).join(Camera).filter(
            Camera.user_id == current_user.id,
            AccessLog.is_known == False
        ).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'enrolled_persons': enrolled_count,
                'total_encodings': total_encodings,
                'access_granted_count': access_granted,
                'unknown_persons_count': unknown_persons,
                'recent_access': [
                    {
                        'person_name': log.person_name,
                        'is_known': log.is_known,
                        'access_granted': log.access_granted,
                        'timestamp': log.timestamp.isoformat()
                    }
                    for log in recent_access
                ]
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
