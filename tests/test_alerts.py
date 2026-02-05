import pytest
from app import create_app, db
from app.models import User, Alert
from app.services.alert_service import AlertService

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

class TestAlerts:
    
    def test_create_alert(self, app):
        with app.app_context():
            user = User(username='test', email='test@example.com')
            user.set_password('Test@123456')
            db.session.add(user)
            db.session.commit()
            
            alert_service = AlertService()
            alert = alert_service.create_alert(
                user_id=user.id,
                alert_type='motion_detected',
                title='Motion Detected',
                message='Motion detected in living room',
                severity='medium'
            )
            
            assert alert.id is not None
            assert alert.user_id == user.id
            assert alert.alert_type == 'motion_detected'
            assert alert.is_read == False
    
    def test_mark_alert_as_read(self, auth_client):
        with auth_client.application.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            alert = Alert(
                user_id=user.id,
                alert_type='test',
                title='Test',
                message='Test message',
                is_read=False
            )
            db.session.add(alert)
            db.session.commit()
            alert_id = alert.id
        
        response = auth_client.post(f'/alerts/{alert_id}/read')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        
        with auth_client.application.app_context():
            alert = Alert.query.get(alert_id)
            assert alert.is_read == True
    
    def test_delete_alert(self, auth_client):
        with auth_client.application.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            alert = Alert(
                user_id=user.id,
                alert_type='test',
                title='Test',
                message='Test message'
            )
            db.session.add(alert)
            db.session.commit()
            alert_id = alert.id
        
        response = auth_client.delete(f'/alerts/{alert_id}/delete')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        
        with auth_client.application.app_context():
            alert = Alert.query.get(alert_id)
            assert alert is None
    
    def test_get_unread_alerts(self, auth_client):
        with auth_client.application.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            
            alert1 = Alert(user_id=user.id, alert_type='test', title='Unread', message='Test', is_read=False)
            alert2 = Alert(user_id=user.id, alert_type='test', title='Read', message='Test', is_read=True)
            
            db.session.add(alert1)
            db.session.add(alert2)
            db.session.commit()
        
        response = auth_client.get('/alerts/unread')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert len(data['alerts']) == 1
        assert data['alerts'][0]['title'] == 'Unread'
    
    def test_clear_all_alerts(self, auth_client):
        with auth_client.application.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            
            for i in range(3):
                alert = Alert(
                    user_id=user.id,
                    alert_type='test',
                    title=f'Alert {i}',
                    message='Test',
                    is_read=False
                )
                db.session.add(alert)
            
            db.session.commit()
        
        response = auth_client.post('/alerts/clear-all')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        
        with auth_client.application.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            unread = Alert.query.filter_by(user_id=user.id, is_read=False).count()
            assert unread == 0
