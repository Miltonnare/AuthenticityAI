import uuid
from fastapi.testclient import TestClient
from app.models.contradiction import Claim

def test_campaign_promise_tracker(client: TestClient, db_session):
    # Setup Admin Token
    client.post(
        "/api/v1/auth/register",
        json={"email": "tracker_tester@authenticity.io", "password": "securepassword"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "tracker_tester@authenticity.io", "password": "securepassword"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Politician
    create_pol = client.post(
        "/api/v1/politicians",
        headers=headers,
        json={"first_name": "Campaign", "last_name": "Runner", "party": "Republican"}
    )
    pol_id = create_pol.json()["id"]

    # 1. Create a Campaign Promise
    promise_res = client.post(
        "/api/v1/promises",
        headers=headers,
        json={
            "politician_id": pol_id,
            "title": "Tax reduction plan",
            "description": "Commitment to lower local business taxes.",
            "category": "Economy"
        }
    )
    assert promise_res.status_code == 201
    promise_id = promise_res.json()["id"]
    assert promise_res.json()["status"] == "proposed"

    # 2. List promises and verify filters
    list_res = client.get(f"/api/v1/promises?politician_id={pol_id}&category=Economy")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["title"] == "Tax reduction plan"

    # 3. Simulate creating opposing statement claim in DB manually
    claim = Claim(
        politician_id=pol_id,
        speech_id=uuid.uuid4(),
        claim_text="We must increase the corporate tax rate next year.",
        embedding=[0.1] * 384,
        category="Economy"
    )
    db_session.add(claim)
    db_session.commit()

    # 4. Attach opposing evidence and assert state transitions to broken
    evidence_res = client.post(
        "/api/v1/promises/evidence",
        headers=headers,
        json={
            "promise_id": promise_id,
            "claim_id": str(claim.id),
            "evidence_type": "opposing_statement",
            "notes": "Statement contradicts the original tax reduction promise."
        }
    )
    assert evidence_res.status_code == 201
    assert evidence_res.json()["notes"] == "Statement contradicts the original tax reduction promise."

    # Verify state transitioned to broken
    get_promise = client.get(f"/api/v1/promises?politician_id={pol_id}")
    assert get_promise.json()[0]["status"] == "broken"

def test_public_api_data_export(client: TestClient, db_session):
    # Setup User Token
    client.post(
        "/api/v1/auth/register",
        json={"email": "dev_user@authenticity.io", "password": "securepassword"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "dev_user@authenticity.io", "password": "securepassword"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Register API key
    key_res = client.post(
        "/api/v1/export/api-keys",
        headers=headers,
        json={"name": "Data Analysis App"}
    )
    assert key_res.status_code == 201
    assert "api_key" in key_res.json()
    assert key_res.json()["name"] == "Data Analysis App"

    # 2. List API keys
    list_res = client.get("/api/v1/export/api-keys", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # Create Politician
    create_pol = client.post(
        "/api/v1/politicians",
        headers=headers,
        json={"first_name": "Export", "last_name": "Pol", "party": "Independent"}
    )
    pol_id = create_pol.json()["id"]

    # 3. Export Data in JSON
    export_json = client.get(f"/api/v1/export/politician/{pol_id}?format=json")
    assert export_json.status_code == 200
    assert export_json.json()["politician"]["first_name"] == "Export"
    assert "claims" in export_json.json()

    # 4. Export Data in CSV
    export_csv = client.get(f"/api/v1/export/politician/{pol_id}?format=csv")
    assert export_csv.status_code == 200
    assert "text/csv" in export_csv.headers["content-type"]

def test_notification_engine(client: TestClient, db_session):
    # Setup User Token
    client.post(
        "/api/v1/auth/register",
        json={"email": "notifier_user@authenticity.io", "password": "securepassword"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "notifier_user@authenticity.io", "password": "securepassword"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Politician
    create_pol = client.post(
        "/api/v1/politicians",
        headers=headers,
        json={"first_name": "Notified", "last_name": "Politician", "party": "Independent"}
    )
    pol_id = create_pol.json()["id"]

    # 1. Subscribe to Politician
    sub_res = client.post(f"/api/v1/notifications/subscribe/{pol_id}", headers=headers)
    assert sub_res.status_code == 200
    assert "subscribed" in sub_res.json()["message"]

    # 2. Register Promise
    promise_res = client.post(
        "/api/v1/promises",
        headers=headers,
        json={
            "politician_id": pol_id,
            "title": "Clean Water Promise",
            "description": "Will construct water filters.",
            "category": "Infrastructure"
        }
    )
    promise_id = promise_res.json()["id"]

    # 3. Add opposing evidence statement to change status to broken
    evidence_res = client.post(
        "/api/v1/promises/evidence",
        headers=headers,
        json={
            "promise_id": promise_id,
            "evidence_type": "opposing_statement",
            "notes": "Statement contradicts construction efforts."
        }
    )
    assert evidence_res.status_code == 201

    # 4. Retrieve notifications and check the alert exists
    notify_res = client.get("/api/v1/notifications", headers=headers)
    assert notify_res.status_code == 200
    assert len(notify_res.json()) == 1
    assert "Promise Status Changed" in notify_res.json()[0]["title"]
    assert "shifted from proposed to broken" in notify_res.json()[0]["body"]

    # 5. Mark all as read
    read_res = client.post("/api/v1/notifications/read-all", headers=headers)
    assert read_res.status_code == 200
    
    # Verify notification is marked as read
    notify_res2 = client.get("/api/v1/notifications", headers=headers)
    assert notify_res2.json()[0]["is_read"] is True
