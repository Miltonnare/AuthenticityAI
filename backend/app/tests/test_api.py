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

def test_ingest_url_and_status(client: TestClient):
    # Register and login admin
    client.post(
        "/api/v1/auth/register",
        json={"email": "ingester@authenticity.io", "password": "securepassword"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "ingester@authenticity.io", "password": "securepassword"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create politician first
    create_pol = client.post(
        "/api/v1/politicians",
        headers=headers,
        json={"first_name": "Ingest", "last_name": "Pol", "party": "Republican"}
    )
    pol_id = create_pol.json()["id"]

    # Ingest URL
    ingest_res = client.post(
        "/api/v1/speeches/ingest/url",
        headers=headers,
        json={
            "politician_id": pol_id,
            "title": "Tax Speech Ingress Test",
            "source_url": "https://www.youtube.com/watch?v=123",
            "media_type": "youtube",
            "date_delivered": "2026-07-27"
        }
    )
    assert ingest_res.status_code == 202
    speech_id = ingest_res.json()["id"]

    # Get status
    status_res = client.get(f"/api/v1/speeches/ingest/{speech_id}/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] in ["queued", "processing", "completed"]

def test_ingest_file(client: TestClient):
    # Login admin
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "ingester@authenticity.io", "password": "securepassword"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create politician first
    create_pol = client.post(
        "/api/v1/politicians",
        headers=headers,
        json={"first_name": "Ingest", "last_name": "Pol2", "party": "Democrat"}
    )
    pol_id = create_pol.json()["id"]

    # Ingest File
    import io
    file_content = b"fake audio content bytes"
    file_io = io.BytesIO(file_content)
    
    ingest_res = client.post(
        "/api/v1/speeches/ingest/file",
        headers=headers,
        data={
            "politician_id": pol_id,
            "title": "Uploaded Speech Ingress Test",
            "date_delivered": "2026-07-27"
        },
        files={"file": ("speech.wav", file_io, "audio/wav")}
    )
    assert ingest_res.status_code == 202
    speech_id = ingest_res.json()["id"]

    # Get status
    status_res = client.get(f"/api/v1/speeches/ingest/{speech_id}/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] in ["queued", "processing", "completed"]

def test_multilingual_speech_processing(client: TestClient, db_session):
    # 1. Setup Admin Token
    client.post(
        "/api/v1/auth/register",
        json={"email": "sw_tester@authenticity.io", "password": "securepassword"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "sw_tester@authenticity.io", "password": "securepassword"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Politician
    create_pol = client.post(
        "/api/v1/politicians",
        headers=headers,
        json={"first_name": "Kiswahili", "last_name": "Speaker", "party": "Independent"}
    )
    pol_id = create_pol.json()["id"]

    # 3. Create Speech with Kiswahili title (triggers mock transcript with Kiswahili text)
    speech_res = client.post(
        "/api/v1/speeches/ingest/url",
        headers=headers,
        json={
            "politician_id": pol_id,
            "title": "Mageuzi ya kodi na bajeti ya serikali",
            "source_url": "https://www.youtube.com/watch?v=sw_test",
            "media_type": "youtube",
            "date_delivered": "2026-07-27"
        }
    )
    assert speech_res.status_code == 202
    speech_id = speech_res.json()["id"]

    # 4. Execute the background task synchronously using db_session
    from app.worker.tasks import process_speech
    task_res = process_speech(speech_id)
    assert task_res["status"] == "completed"

    # 5. Verify database records have translations and language code updates
    from app.models.speech import TranscriptSegment, Speech
    from app.models.contradiction import Claim

    speech_record = db_session.query(Speech).filter(Speech.id == speech_id).first()
    assert speech_record.status == "completed"

    segments = db_session.query(TranscriptSegment).filter(TranscriptSegment.speech_id == speech_id).all()
    assert len(segments) > 0
    
    # Check that Kiswahili segments were translated and tagged
    kiswahili_segs = [s for s in segments if s.language_code == "sw"]
    assert len(kiswahili_segs) > 0
    for s in kiswahili_segs:
        assert s.translated_text is not None
        assert s.text_content in TRANSLATION_MAP_KEYS_CHECK(s.text_content)

    claims = db_session.query(Claim).filter(Claim.speech_id == speech_id).all()
    assert len(claims) > 0
    for c in claims:
        assert c.language_code == "sw"
        assert c.original_claim_text is not None
        # Verify that the search text of the claim is stored in translated English
        assert c.claim_text != c.original_claim_text

def TRANSLATION_MAP_KEYS_CHECK(text: str) -> list:
    return [
        "Mimi sijawahi kupendekeza nyongeza ya kodi ya mauzo.",
        "Lazima tuongeze mapato ya serikali kwa kupandisha kodi ya mauzo hadi asilimia tano.",
        "Habari za asubuhi. Ningependa kuzungumzia kuhusu bajeti na mageuzi ya kodi."
    ]
