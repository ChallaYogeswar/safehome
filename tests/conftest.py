import pytest
import os
import sys
from app import create_app, db as _db
from app.models import User
from config import TestingConfig

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope='module')
def app():
    app = create_app('testing')
    
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture(scope='module')
def client(app):
    return app.test_client()

@pytest.fixture(scope='module')
def runner(app):
    return app.test_cli_runner()

@pytest.fixture(scope='function')
def db(app):
    _db.session.begin_nested()
    yield _db
    _db.session.rollback()

@pytest.fixture(scope='function')
def user(db):
    user = User(username='testuser', email='test@example.com')
    user.set_password('password')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture(scope='function')
def auth(client, user):
    return AuthActions(client)

class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, username='testuser', password='password'):
        return self._client.post(
            '/auth/login',
            data={'username': username, 'password': password},
            follow_redirects=True
        )

    def logout(self):
        return self._client.get('/auth/logout', follow_redirects=True)
