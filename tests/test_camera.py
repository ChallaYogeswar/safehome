import pytest
from app import create_app, db
from app.models import User, Camera, Detection
import base64

@pytest.fixture
def app():
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    user = User(username='testuser', email='test@example.com')
    user.set_password('Test@123456')
    user.is_verified = True
    
    with client.application.app_context():
        db.session.add(user)
        db.session.commit()
        
        client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'Test@123456'
        })
    
    return client

class TestCamera:
    
    def test_add_camera(self, auth_client):
        response = auth_client.post('/camera/add', 
            json={
                'name': 'Test Camera',
                'location': 'Living Room'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert data['camera']['name'] == 'Test Camera'
    
    def test_add_camera_no_name(self, auth_client):
        response = auth_client.post('/camera/add', 
            json={
                'location': 'Living Room'
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] == False
    
    def test_update_camera(self, auth_client):
        with auth_client.application.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            camera = Camera(user_id=user.id, name='Old Name', location='Old Location')
            db.session.add(camera)
            db.session.commit()
            camera_id = camera.id
        
        response = auth_client.put(f'/camera/{camera_id}/update',
            json={
                'name': 'New Name',
                'location': 'New Location'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        
        with auth_client.application.app_context():
            camera = Camera.query.get(camera_id)
            assert camera.name == 'New Name'
            assert camera.location == 'New Location'
    
    def test_delete_camera(self, auth_client):
        with auth_client.application.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            camera = Camera(user_id=user.id, name='Test Camera')
            db.session.add(camera)
            db.session.commit()
            camera_id = camera.id
        
        response = auth_client.delete(f'/camera/{camera_id}/delete')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        
        with auth_client.application.app_context():
            camera = Camera.query.get(camera_id)
            assert camera is None
    
    def test_get_camera_stats(self, auth_client):
        with auth_client.application.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            camera = Camera(user_id=user.id, name='Test Camera')
            db.session.add(camera)
            db.session.commit()
            
            detection = Detection(
                camera_id=camera.id,
                detection_type='motion',
                confidence=0.95
            )
            db.session.add(detection)
            db.session.commit()
            
            camera_id = camera.id
        
        response = auth_client.get(f'/camera/{camera_id}/stats')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert data['stats']['total_detections'] >= 1
    
    def test_unauthorized_camera_access(self, client):
        response = client.post('/camera/add',
            json={'name': 'Test Camera'}
        )
        
        assert response.status_code == 302 or response.status_code == 401
    
    def test_camera_not_found(self, auth_client):
        response = auth_client.get('/camera/99999/stats')
        
        assert response.status_code == 404
