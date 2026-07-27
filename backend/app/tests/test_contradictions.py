import uuid
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.models.contradiction import Claim, Contradiction, AuditLog, Citation
from app.models.feedback import FeedbackReport

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

def test_moderation_portal_rbac(client: TestClient, db_session):
    # Register standard user (defaults to user since count > 0)
    client.post(
        "/api/v1/auth/register",
        json={"email": "standard_user@authenticity.io", "password": "userpassword"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "standard_user@authenticity.io", "password": "userpassword"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Query moderation queue - should be forbidden (403)
    queue_res = client.get("/api/v1/admin/contradictions/queue", headers=headers)
    assert queue_res.status_code == 403

    # Post review - should be forbidden (403)
    review_res = client.post(
        f"/api/v1/admin/contradictions/{uuid.uuid4()}/review",
        headers=headers,
        json={"review_status": "verified"}
    )
    assert review_res.status_code == 403

def test_external_audit_trails(client: TestClient, db_session):
    # Setup Admin Token
    client.post(
        "/api/v1/auth/register",
        json={"email": "audit_tester@authenticity.io", "password": "securepassword"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "audit_tester@authenticity.io", "password": "securepassword"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Politician & Claims & Contradiction
    create_pol = client.post(
        "/api/v1/politicians",
        headers=headers,
        json={"first_name": "Audit", "last_name": "Pol", "party": "Independent"}
    )
    pol_id = create_pol.json()["id"]

    claim1 = Claim(politician_id=pol_id, speech_id=uuid.uuid4(), claim_text="Tax is good.", embedding=[0.1]*384)
    claim2 = Claim(politician_id=pol_id, speech_id=uuid.uuid4(), claim_text="Tax is bad.", embedding=[0.11]*384)
    db_session.add(claim1)
    db_session.add(claim2)
    db_session.commit()

    contra = Contradiction(original_claim_id=claim1.id, contradicting_claim_id=claim2.id, confidence_score=0.9, explanation="Tax stance contradictions")
    db_session.add(contra)
    db_session.commit()

    # 1. Post a review (triggers chained audit log creation)
    review_res = client.post(
        f"/api/v1/admin/contradictions/{contra.id}/review",
        headers=headers,
        json={"review_status": "verified", "review_notes": "Reviewed for cryptographic audit test."}
    )
    assert review_res.status_code == 200

    # 2. Retrieve public logs and verify hash chaining
    logs_res = client.get("/api/v1/audit/logs")
    assert logs_res.status_code == 200
    logs = logs_res.json()
    assert len(logs) > 0
    assert logs[-1]["signature_hash"] is not None
    assert logs[-1]["prev_hash"] is not None

    # 3. Verify ledger integrity
    verify_res = client.get("/api/v1/audit/verify")
    assert verify_res.status_code == 200
    assert verify_res.json()["is_valid"] is True

    # 4. Tamper with a log payload manually
    db_log = db_session.query(AuditLog).filter(AuditLog.target_id == contra.id).first()
    assert db_log is not None
    db_log.payload = '{"tampered": "payload"}'
    db_session.commit()

    # 5. Verify ledger integrity again - should detect tampering!
    verify_res2 = client.get("/api/v1/audit/verify")
    assert verify_res2.status_code == 200
    assert verify_res2.json()["is_valid"] is False
    assert verify_res2.json()["tampered_log_id"] == str(db_log.id)

def test_user_feedback_loops(client: TestClient, db_session):
    # Setup User Token
    client.post(
        "/api/v1/auth/register",
        json={"email": "feedback_user@authenticity.io", "password": "securepassword"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "feedback_user@authenticity.io", "password": "securepassword"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Setup Admin Token
    client.post(
        "/api/v1/auth/register",
        json={"email": "feedback_admin@authenticity.io", "password": "securepassword"}
    )
    db_session.execute(
        text("UPDATE users SET role = 'admin' WHERE email = 'feedback_admin@authenticity.io'")
    )
    db_session.commit()
    
    login_admin = client.post(
        "/api/v1/auth/login",
        data={"username": "feedback_admin@authenticity.io", "password": "securepassword"}
    )
    admin_token = login_admin.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create Politician & Claims & Contradiction
    create_pol = client.post(
        "/api/v1/politicians",
        headers=admin_headers,
        json={"first_name": "Feedback", "last_name": "Pol", "party": "Independent"}
    )
    pol_id = create_pol.json()["id"]

    claim1 = Claim(politician_id=pol_id, speech_id=uuid.uuid4(), claim_text="Tax is good.", embedding=[0.1]*384)
    claim2 = Claim(politician_id=pol_id, speech_id=uuid.uuid4(), claim_text="Tax is bad.", embedding=[0.11]*384)
    db_session.add(claim1)
    db_session.add(claim2)
    db_session.commit()

    contra = Contradiction(original_claim_id=claim1.id, contradicting_claim_id=claim2.id, confidence_score=0.9, explanation="Tax stance contradictions", review_status="verified")
    db_session.add(contra)
    db_session.commit()

    # 1. Post a context suggestion
    suggestion_res = client.post(
        "/api/v1/feedback",
        headers=headers,
        json={
            "target_id": claim1.id,
            "target_type": "claim",
            "report_type": "context_omission",
            "description": "Suggested missing context notes."
        }
    )
    assert suggestion_res.status_code == 201

    # 2. Get admin suggestions queue
    queue_res = client.get("/api/v1/admin/feedback/queue", headers=admin_headers)
    assert queue_res.status_code == 200
    assert len(queue_res.json()) >= 1
    assert queue_res.json()[0]["report_type"] == "context_omission"

    # 3. Seed 5 verification challenges on the verified contradiction
    for i in range(5):
        client.post(
            "/api/v1/feedback",
            headers=headers,
            json={
                "target_id": contra.id,
                "target_type": "contradiction",
                "report_type": "verification_challenge",
                "description": f"Auditor dispute {i}."
            }
        )

    # 4. Check contradiction status - should have shifted back to pending_review!
    db_session.refresh(contra)
    assert contra.review_status == "pending_review"
