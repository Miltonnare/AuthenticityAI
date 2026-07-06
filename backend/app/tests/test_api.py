import pytest
from fastapi.testclient import TestClient

def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_auth_flow(client: TestClient):
    # 1. Register User
    reg_response = client.post(
        "/api/v1/auth/register",
        json={"email": "tester@authenticity.io", "password": "securepassword123"}
    )
    assert reg_response.status_code == 201
    assert reg_response.json()["email"] == "tester@authenticity.io"
    # First user registered in tests defaults to 'admin' (based on count checker in auth.py)
    assert reg_response.json()["role"] == "admin"

    # 2. Login User
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "tester@authenticity.io", "password": "securepassword123"}
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    # 3. Retrieve Self Profile
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "tester@authenticity.io"

def test_create_politician_requires_auth(client: TestClient):
    # Post without authentication header
    response = client.post(
        "/api/v1/politicians",
        json={"first_name": "Jane", "last_name": "Smith", "party": "Independent"}
    )
    assert response.status_code == 401 # Unauthorized

def test_politician_crud(client: TestClient):
    # Register and get admin token
    client.post(
        "/api/v1/auth/register",
        json={"email": "admin@authenticity.io", "password": "adminpassword"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@authenticity.io", "password": "adminpassword"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Politician
    create_res = client.post(
        "/api/v1/politicians",
        headers=headers,
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "party": "Democrat",
            "current_office": "Senator",
            "bio": "Senator bio text",
            "image_url": "http://example.com/jane.jpg"
        }
    )
    assert create_res.status_code == 201
    politician_id = create_res.json()["id"]

    # Get Politician
    get_res = client.get(f"/api/v1/politicians/{politician_id}")
    assert get_res.status_code == 200
    assert get_res.json()["last_name"] == "Doe"

    # List Politicians
    list_res = client.get("/api/v1/politicians")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
