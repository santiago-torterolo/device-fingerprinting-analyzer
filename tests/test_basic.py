import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_homepage(client):
    """Test that the dashboard loads correctly"""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Dashboard" in response.data

def test_api_devices(client):
    """Test that the API returns JSON"""
    response = client.get('/api/devices')
    assert response.status_code == 200
    assert response.is_json
