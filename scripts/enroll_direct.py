from app import create_app
from app.models import db, User, Camera
from app.services.face_recognition_service import FaceRecognitionService
import os
from PIL import Image, ImageDraw

APP = create_app()
UPLOAD_DIR = 'uploads/faces'
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

with APP.app_context():
    # Create test user
    user = User.query.filter_by(email='direct_test@example.com').first()
    if not user:
        user = User(username='directtest', email='direct_test@example.com')
        user.set_password('Test@1234')
        user.is_verified = True
        db.session.add(user)
        db.session.commit()
        print('Created user', user.id)
    else:
        print('User exists', user.id)

    # Ensure a camera exists
    camera = Camera.query.filter_by(user_id=user.id).first()
    if not camera:
        camera = Camera(user_id=user.id, name='Test Cam')
        db.session.add(camera)
        db.session.commit()
        print('Created camera', camera.id)
    else:
        print('Camera exists', camera.id)

    # Create two sample images
    img_paths = []
    for i in range(2):
        img = Image.new('RGB', (200,200), color=(73,109,137))
        d = ImageDraw.Draw(img)
        d.ellipse((60,50,140,130), fill=(255,224,189))
        d.ellipse((80,80,95,95), fill=(0,0,0))
        d.ellipse((105,80,120,95), fill=(0,0,0))
        d.arc((80,110,120,140), 0, 180, fill=(0,0,0), width=3)
        path = os.path.join(UPLOAD_DIR, f'direct_image_{user.id}_{i+1}.jpg')
        img.save(path)
        img_paths.append(path)
    print('Images created:', img_paths)

    # Enroll person
    result = FaceRecognitionService.enroll_person(user.id, 'Direct Test', img_paths, relation='family', is_resident=True)
    print('Enroll result:', result)

    # Try encoding one image
    enc = FaceRecognitionService.encode_image_file(img_paths[0])
    print('Encodings:', enc)
    if enc:
        encoding = enc[0]['encoding']
        rec = FaceRecognitionService.recognize_face(camera.id, encoding)
        print('Recognition:', rec)
    else:
        print('No face encoding detected in sample image')
