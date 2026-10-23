import copy
import pytest
from fastapi.testclient import TestClient
from backend import app, SESSIONS
from tool_engine import CATALOG

@pytest.fixture
def client():
    SESSIONS.clear()
    with TestClient(app, base_url='http://127.0.0.1:8000') as c:
        yield c

def headers(client):
    result = client.post('/api/session').json()
    return {'X-CSRF-Token': result['csrf']}

def test_health_and_frontend(client):
    assert client.get('/api/health').json()['protocol'] == 'galactica-v3'
    assert 'ACADEMIA' in client.get('/').text

def test_no_session(client):
    assert client.post('/api/execute', json={'name':'localizar_baliza','arguments':{'sector':'DAGOBAH'}}).status_code == 401

def test_csrf(client):
    headers(client)
    assert client.post('/api/execute', json={'name':'localizar_baliza','arguments':{'sector':'DAGOBAH'}}).status_code == 403

def test_cross_origin_and_host(client):
    assert client.post('/api/session', headers={'Origin':'https://example.com'}).status_code == 403
    assert client.get('/api/health', headers={'Host':'evil.test'}).status_code == 403

def test_calculation_real_python(client):
    response = client.post('/api/execute', headers=headers(client), json={'call_id':'test-read','name':'calcular_reserva','arguments':{'combustible':60,'consumo':32}})
    assert response.status_code == 200
    result = response.json()
    assert result['data']['reserva'] == 28
    assert result['meta']['runtime'] == 'python-local'

def test_cannot_assign_role_in_payload(client):
    response = client.post('/api/execute', headers=headers(client), json={'name':'localizar_baliza','arguments':{'sector':'DAGOBAH'},'role':'admin'})
    assert response.status_code == 422

def test_same_origin_approved_write_and_replay(client):
    h = headers(client)
    h['Origin'] = 'http://127.0.0.1:8000'
    body = {'name':'despachar_rescate','arguments':copy.deepcopy(CATALOG['despachar_rescate']['example'])}
    assert client.post('/api/execute', headers=h, json=body).json()['error']['code'] == 'CONFIRMATION_REQUIRED'
    p = client.post('/api/approve', headers=h, json=body).json()
    one = client.post('/api/execute', headers=h, json={**body,'approval_token':p['approval_token']}).json()
    two = client.post('/api/execute', headers=h, json=body).json()
    assert one['ok'] and two['data']['replayed']
    assert one['data']['order_id'] == two['data']['order_id']
