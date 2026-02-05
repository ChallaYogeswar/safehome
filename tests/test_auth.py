import pytest
from app import create_app, db
from app.models import User
from flask import url_for

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

class TestAuth:
    
    def test_register_success(self, client):
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'New@123456',
            'confirm_password': 'New@123456'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Registration successful' in response.data or b'login' in response.data.lower()
        
        with client.application.app_context():
            user = User.query.filter_by(email='new@example.com').first()
            assert user is not None
            assert user.username == 'newuser'
    
    def test_register_duplicate_email(self, client):
        user = User(username='existing', email='existing@example.com')
        user.set_password('Test@123456')
        
        with client.application.app_context():
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'existing@example.com',
            'password': 'New@123456',
            'confirm_password': 'New@123456'
        })
        
        assert b'Email already registered' in response.data
    
    def test_register_weak_password(self, client):
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'weak',
            'confirm_password': 'weak'
        })
        
        assert response.status_code == 200
        assert b'Password must be at least' in response.data
    
    def test_login_success(self, client):
        user = User(username='testuser', email='test@example.com')
        user.set_password('Test@123456')
        user.is_verified = True
        
        with client.application.app_context():
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'Test@123456'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_login_invalid_password(self, client):
        user = User(username='testuser', email='test@example.com')
        user.set_password('Test@123456')
        
        with client.application.app_context():
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'WrongPassword'
        })
        
        assert b'Invalid email or password' in response.data
    
    def test_login_nonexistent_user(self, client):
        response = client.post('/auth/login', data={
            'email': 'nonexistent@example.com',
            'password': 'Test@123456'
        })
        
        assert b'Invalid email or password' in response.data
    
    def test_logout(self, auth_client):
        response = auth_client.get('/auth/logout', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'logged out' in response.data.lower()
    
    def test_password_hashing(self, app):
        with app.app_context():
            user = User(username='test', email='test@example.com')
            user.set_password('Test@123456')
            
            assert user.password_hash != 'Test@123456'
            assert user.check_password('Test@123456')
            assert not user.check_password('WrongPassword')
    
    def test_account_lockout(self, client):
        user = User(username='testuser', email='test@example.com')
        user.set_password('Test@123456')
        
        with client.application.app_context():
            db.session.add(user)
            db.session.commit()
        
        for i in range(5):
            client.post('/auth/login', data={
                'email': 'test@example.com',
                'password': 'WrongPassword'
            })
        
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'Test@123456'
        })
        
        with client.application.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            assert user.locked_until is not None
