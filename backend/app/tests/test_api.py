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
    from app.worker.tasks import process_speech
    task_res = process_speech(speech_id)
    assert task_res["status"] == "completed"

    # Verify that the DB contains decomposed claims
    from app.models.contradiction import Claim
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
    from app.models.contradiction import Claim
    import uuid
    claim = Claim(
        politician_id=pol_id,
        speech_id=uuid.uuid4(), # dummy uuid
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

def test_fact_verification_workflow(client: TestClient, db_session):
    # Setup Admin Token
    client.post(
        "/api/v1/auth/register",
        json={"email": "moderator_tester@authenticity.io", "password": "securepassword"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "moderator_tester@authenticity.io", "password": "securepassword"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Politician
    create_pol = client.post(
        "/api/v1/politicians",
        headers=headers,
        json={"first_name": "Moderated", "last_name": "Pol", "party": "Independent"}
    )
    pol_id = create_pol.json()["id"]

    # Simulate two claims and a contradiction manually in DB
    from app.models.contradiction import Claim, Contradiction, AuditLog, Citation
    import uuid
    
    claim1 = Claim(
        politician_id=pol_id,
        speech_id=uuid.uuid4(),
        claim_text="I support tax reduction.",
        embedding=[0.1] * 384,
        category="General"
    )
    claim2 = Claim(
        politician_id=pol_id,
        speech_id=uuid.uuid4(),
        claim_text="I oppose tax reduction.",
        embedding=[0.1] * 384,
        category="General"
    )
    db_session.add(claim1)
    db_session.add(claim2)
    db_session.flush()

    contra = Contradiction(
        original_claim_id=claim1.id,
        contradicting_claim_id=claim2.id,
        confidence_score=0.88,
        explanation="Claims display opposing tax policy stances."
    )
    db_session.add(contra)
    db_session.commit()

    # Call review/verify endpoint
    review_res = client.post(
        f"/api/v1/admin/contradictions/{contra.id}/review",
        headers=headers,
        json={
            "review_status": "verified",
            "review_notes": "Citations support voting records of stance contradiction.",
            "citations": [
                {
                    "title": "Treasury tax reports 2026",
                    "url": "https://government.gov/treasury",
                    "source_name": "Treasury Department",
                    "published_date": "2026-07-27"
                }
            ]
        }
    )
    assert review_res.status_code == 200
    assert review_res.json()["review_status"] == "verified"
    assert review_res.json()["review_notes"] == "Citations support voting records of stance contradiction."
    assert len(review_res.json()["citations"]) == 1

    # Verify Audit Log and Citation exist in DB
    audit = db_session.query(AuditLog).filter(AuditLog.target_id == contra.id).first()
    assert audit is not None
    assert audit.action == "verified_contradiction"
    assert "Treasury tax reports" in audit.payload

    citation = db_session.query(Citation).filter(Citation.contradiction_id == contra.id).first()
    assert citation is not None
    assert citation.title == "Treasury tax reports 2026"

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
    source_id = source_res.json()["id"]

    # 2. List media sources
    list_res = client.get("/api/v1/sources")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["name"] == "Parliamentary Hansard Portal"
