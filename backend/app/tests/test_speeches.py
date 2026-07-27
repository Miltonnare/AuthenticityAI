import io
import pytest
from fastapi.testclient import TestClient
from app.models.speech import TranscriptSegment, Speech
from app.models.contradiction import Claim
from app.worker.tasks import process_speech, transcribe_audio_chunk

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

    # 3. Create Speech with Kiswahili title
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

    # 4. Execute the background task synchronously
    task_res = process_speech(speech_id)
    assert task_res["status"] == "completed"

    # 5. Verify database records
    speech_record = db_session.query(Speech).filter(Speech.id == speech_id).first()
    assert speech_record.status == "completed"

    segments = db_session.query(TranscriptSegment).filter(TranscriptSegment.speech_id == speech_id).all()
    assert len(segments) > 0
    
    # Check that Kiswahili segments were translated and tagged
    kiswahili_segs = [s for s in segments if s.language_code == "sw"]
    assert len(kiswahili_segs) > 0
    for s in kiswahili_segs:
        assert s.translated_text is not None
        assert s.text_content in [
            "Mimi sijawahi kupendekeza nyongeza ya kodi ya mauzo.",
            "Lazima tuongeze mapato ya serikali kwa kupandisha kodi ya mauzo hadi asilimia tano.",
            "Habari za asubuhi. Ningependa kuzungumzia kuhusu bajeti na mageuzi ya kodi."
        ]

    claims = db_session.query(Claim).filter(Claim.speech_id == speech_id).all()
    assert len(claims) > 0
    for c in claims:
        assert c.language_code == "sw"
        assert c.original_claim_text is not None
        assert c.claim_text != c.original_claim_text

def test_media_processing_chunking(db_session):
    mock_segments = [
        {"text": "First segment speech.", "start": 0.0, "end": 10.0},
        {"text": "Second segment speech.", "start": 10.0, "end": 20.0}
    ]
    
    offset = 180.0
    results = transcribe_audio_chunk(mock_segments, offset)
    
    assert len(results) == 2
    assert results[0]["start_time"] == 180.0
    assert results[0]["end_time"] == 190.0
    assert results[0]["text_content"] == "First segment speech."
    assert results[1]["start_time"] == 190.0
    assert results[1]["end_time"] == 200.0
