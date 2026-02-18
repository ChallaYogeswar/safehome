import pytest
from app.models import AccessLog, Camera, User, db

@pytest.fixture
def test_camera(user, app):
    camera = Camera(user_id=user.id, name='Test Cam')
    db.session.add(camera)
    db.session.commit()
    return camera

@pytest.fixture
def access_log(user, test_camera, app):
    log = AccessLog(
        camera_id=test_camera.id,
        person_name='Test Person',
        is_known=True,
        confidence=0.95,
        access_granted=False,
        action='pending_approval'
    )
    db.session.add(log)
    db.session.commit()
    return log

class TestEntriesRoutes:
    def test_list_entries(self, client, auth, access_log):
        auth.login()
        response = client.get('/entries/list')
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert len(data['entries']) >= 1
        assert data['entries'][0]['person_name'] == 'Test Person'

    def test_filter_entries(self, client, auth, access_log):
        auth.login()
        # Create another diverse log
        log2 = AccessLog(
            camera_id=access_log.camera_id,
            person_name='Unknown',
            is_known=False,
            action='alert_sent'
        )
        db.session.add(log2)
        db.session.commit()

        # Test filter known
        response = client.get('/entries/list?is_known=true')
        data = response.json
        assert len(data['entries']) == 1
        assert data['entries'][0]['person_name'] == 'Test Person'

        # Test filter unknown
        response = client.get('/entries/list?is_known=false')
        data = response.json
        assert len(data['entries']) == 1
        assert data['entries'][0]['person_name'] == 'Unknown'

    def test_approve_entry(self, client, auth, access_log):
        auth.login()
        # Approval endpoint (assuming implementation logic is correct)
        response = client.post(f'/entries/approve/{access_log.id}')
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert data['entry']['action'] == 'door_opened'
        
        # Verify db update
        updated_log = AccessLog.query.get(access_log.id)
        assert updated_log.action == 'door_opened'
        assert updated_log.access_granted is True
        assert updated_log.approved_by is not None

    def test_deny_entry(self, client, auth, access_log):
        auth.login()
        response = client.post(f'/entries/deny/{access_log.id}')
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert data['entry']['action'] == 'entry_denied'
        
        updated_log = AccessLog.query.get(access_log.id)
        assert updated_log.action == 'entry_denied'
        assert updated_log.access_granted is False
