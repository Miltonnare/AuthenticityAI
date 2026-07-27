import uuid
from fastapi.testclient import TestClient
from app.models.contradiction import Claim
from app.worker.tasks import process_speech

def test_advanced_claim_extraction(client: TestClient, db_session):
    # Setup Admin Token
    client.post(
        "/api/v1/auth/register",
        json={"email": "srl_tester@authenticity.io", "password": "securepassword"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "srl_tester@authenticity.io", "password": "securepassword"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Politician
    create_pol = client.post(
        "/api/v1/politicians",
        headers=headers,
        json={"first_name": "SRL", "last_name": "Speaker", "party": "Independent"}
    )
    pol_id = create_pol.json()["id"]

    # Create Speech with a title that has "because" to trigger mock SRL splitting
    speech_res = client.post(
        "/api/v1/speeches/ingest/url",
        headers=headers,
        json={
            "politician_id": pol_id,
            "title": "We will protect local infrastructure because the highway tax rate is 5 percent",
            "source_url": "https://www.youtube.com/watch?v=srl_test",
            "media_type": "youtube",
            "date_delivered": "2026-07-27"
        }
    )
    assert speech_res.status_code == 202
    speech_id = speech_res.json()["id"]

    # Execute the background task
    task_res = process_speech(speech_id)
    assert task_res["status"] == "completed"

    # Verify that the DB contains decomposed claims
    claims = db_session.query(Claim).filter(Claim.speech_id == speech_id).all()
    assert len(claims) > 0

    decomposed_claims = [c for c in claims if c.is_decomposed]
    assert len(decomposed_claims) > 0

    # Ensure parent/child relationships were mapped
    children = [c for c in decomposed_claims if c.parent_claim_id is not None]
    parents = [c for c in decomposed_claims if c.parent_claim_id is None]
    
    assert len(parents) > 0
    assert len(children) > 0
    for child in children:
        assert child.parent_claim_id in [p.id for p in parents]
        
    # Verify that typology checks are operating
    typologies = [c.typology for c in claims]
    assert "promise" in typologies or "statistical" in typologies

def test_source_credibility_engine(client: TestClient, db_session):
    # Setup Admin Token
    client.post(
        "/api/v1/auth/register",
        json={"email": "source_tester@authenticity.io", "password": "securepassword"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "source_tester@authenticity.io", "password": "securepassword"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Register a media source
    source_res = client.post(
        "/api/v1/sources",
        headers=headers,
        json={
            "name": "Parliamentary Hansard Portal",
            "classification": "official",
            "base_score": 1.00,
            "website_url": "https://parliament.gov"
        }
    )
    assert source_res.status_code == 201

    # 2. List media sources
    list_res = client.get("/api/v1/sources")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["name"] == "Parliamentary Hansard Portal"

def test_advanced_semantic_search(client: TestClient, db_session):
    # Setup Admin Token
    client.post(
        "/api/v1/auth/register",
        json={"email": "search_tester2@authenticity.io", "password": "securepassword"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "search_tester2@authenticity.io", "password": "securepassword"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create two politicians
    create_pol1 = client.post(
        "/api/v1/politicians",
        headers=headers,
        json={"first_name": "Searcher", "last_name": "One", "party": "Independent"}
    )
    pol1_id = create_pol1.json()["id"]

    create_pol2 = client.post(
        "/api/v1/politicians",
        headers=headers,
        json={"first_name": "Searcher", "last_name": "Two", "party": "Independent"}
    )
    pol2_id = create_pol2.json()["id"]

    # Seed two claims for different politicians manually in DB
    claim1 = Claim(
        politician_id=pol1_id,
        speech_id=uuid.uuid4(),
        claim_text="Corporate taxes are too high.",
        embedding=[0.1] * 384,
        category="General"
    )
    claim2 = Claim(
        politician_id=pol2_id,
        speech_id=uuid.uuid4(),
        claim_text="Business tax cuts are vital.",
        embedding=[0.11] * 384,
        category="General"
    )
    db_session.add(claim1)
    db_session.add(claim2)
    db_session.commit()

    # 1. Run hybrid search query
    search_res = client.get("/api/v1/search/claims/hybrid?q=taxes")
    assert search_res.status_code == 200
    assert len(search_res.json()) > 0
    assert "Corporate taxes" in search_res.json()[0]["claim_text"]

    # 2. Query related claims
    related_res = client.get(f"/api/v1/search/claims/{claim1.id}/related?limit=5")
    assert related_res.status_code == 200
    assert len(related_res.json()) > 0
    assert related_res.json()[0]["politician_id"] == pol2_id
