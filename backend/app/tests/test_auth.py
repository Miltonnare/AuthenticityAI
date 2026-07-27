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
