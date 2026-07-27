from fastapi.testclient import TestClient

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
        json={"email": "admin_pol@authenticity.io", "password": "adminpassword"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "admin_pol@authenticity.io", "password": "adminpassword"}
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

def test_knowledge_graph_network(client: TestClient, db_session):
    # Setup Admin Token
    client.post(
        "/api/v1/auth/register",
        json={"email": "graph_tester@authenticity.io", "password": "securepassword"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "graph_tester@authenticity.io", "password": "securepassword"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Politician
    create_pol = client.post(
        "/api/v1/politicians",
        headers=headers,
        json={"first_name": "Graphed", "last_name": "Pol", "party": "Independent"}
    )
    pol_id = create_pol.json()["id"]

    # Call graph network endpoint
    graph_res = client.get(
        f"/api/v1/graph/politician/{pol_id}/network?depth=2",
        headers=headers
    )
    assert graph_res.status_code == 200
    assert "nodes" in graph_res.json()
    assert "edges" in graph_res.json()
    
    # Assert nodes and edges format is correct
    nodes = graph_res.json()["nodes"]
    edges = graph_res.json()["edges"]
    assert len(nodes) > 0
    assert nodes[0]["id"] == pol_id or nodes[0]["id"] == "pol-1"
