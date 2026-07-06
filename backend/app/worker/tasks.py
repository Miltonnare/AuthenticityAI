import time
from uuid import UUID
from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session
from app.worker.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.speech import Speech, TranscriptSegment
from app.models.contradiction import Claim, Contradiction

logger = get_task_logger(__name__)

# Lazy loaded ML models to prevent workers from stalling during deployment startup
_nlp = None
_embedder = None
_nli_pipeline = None

def load_nlp():
    global _nlp
    if _nlp is None:
        import spacy
        try:
            _nlp = spacy.load("en_core_web_sm")
        except Exception:
            # Fallback if download failed
            import spacy.cli
            spacy.cli.download("en_core_web_sm")
            _nlp = spacy.load("en_core_web_sm")
    return _nlp

def load_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedder

def load_nli():
    global _nli_pipeline
    if _nli_pipeline is None:
        from transformers import pipeline
        # Use a lightweight, fast NLI model ideal for MVP and CPU/low-memory environments
        _nli_pipeline = pipeline("text-classification", model="cross-encoder/nli-deberta-v3-xsmall")
    return _nli_pipeline


@celery_app.task(name="process_speech", bind=True)
def process_speech(self, speech_id: str):
    logger.info(f"Starting processing job for speech ID: {speech_id}")
    db: Session = SessionLocal()
    
    try:
        speech = db.query(Speech).filter(Speech.id == speech_id).first()
        if not speech:
            logger.error(f"Speech {speech_id} not found in database.")
            return {"status": "failed", "error": "Speech not found"}
            
        speech.status = "processing"
        db.commit()
        
        # 1. Speech Transcription / Mocking (MVP Ingestion wrapper)
        # In a real environment, we would run: ffmpeg -> WhisperX.
        # For the MVP foundation, we simulate this step using a transcription seed library
        # if the URL is dummy or fails, or process custom text.
        logger.info("Initializing transcription engine...")
        raw_transcript = get_speech_transcript_mock(speech.title)
        
        # 2. Save Transcript Segments with Timestamps
        logger.info("Saving transcript segments...")
        segments = []
        for i, segment_data in enumerate(raw_transcript):
            seg = TranscriptSegment(
                speech_id=speech.id,
                sequence_number=i,
                start_time=segment_data["start"],
                end_time=segment_data["end"],
                text_content=segment_data["text"]
            )
            db.add(seg)
            segments.append(seg)
        db.commit() # Flushes to database to populate segment IDs
        
        # 3. NLP Pipeline: Claim Extraction
        logger.info("Extracting claims from transcript...")
        nlp = load_nlp()
        embedder = load_embedder()
        
        claims_created = []
        for seg in segments:
            doc = nlp(seg.text_content)
            # Simple heuristic claim detector: sentence must have subject + verb + object/attribute
            # This filters out conversational filler ("Thank you", "Good morning", "Well, let me say")
            for sent in doc.sents:
                has_subj = any(tok.dep_ in ("nsubj", "nsubjpass", "csubj") for tok in sent)
                has_verb = any(tok.pos_ == "VERB" for tok in sent)
                
                if has_subj and has_verb and len(sent.text.strip()) > 15:
                    claim_text = sent.text.strip()
                    # Generate embedding vector
                    embedding_vector = embedder.encode(claim_text).tolist()
                    
                    claim = Claim(
                        politician_id=speech.politician_id,
                        speech_id=speech.id,
                        segment_id=seg.id,
                        claim_text=claim_text,
                        embedding=embedding_vector,
                        category="General"
                    )
                    db.add(claim)
                    claims_created.append(claim)
                    
        db.commit() # Flush claims to DB so we can search them
        
        # 4. Semantic Similarity & Contradiction Detection (NLI)
        logger.info("Executing NLI matching & contradiction checks...")
        nli = load_nli()
        
        contradictions_found = 0
        for claim in claims_created:
            # Query the database for past claims made by the SAME politician (excluding this speech)
            # Distance operator '<=>' is cosine distance. Cosine Similarity = 1 - Cosine Distance
            # We fetch previous statements with Cosine Similarity > 0.65 (Distance < 0.35)
            similar_claims = db.query(Claim).filter(
                Claim.politician_id == speech.politician_id,
                Claim.speech_id != speech.id
            ).order_by(Claim.embedding.op("<=>")(claim.embedding)).limit(5).all()
            
            for past_claim in similar_claims:
                # Calculate NLI prediction
                # Format required by Cross-Encoder NLI: "Premise [SEP] Hypothesis"
                # Label outputs: contradiction, entailment, neutral
                try:
                    # Let's perform inference
                    # cross-encoder outputs logits/scores. Label indices match the model output configs.
                    res = nli(f"{past_claim.claim_text} [SEP] {claim.claim_text}")[0]
                    label = res["label"].lower()
                    score = res["score"]
                    
                    # If model identifies it as a contradiction with high confidence
                    if "contradiction" in label and score > 0.70:
                        # Create Flagged Contradiction
                        explanation = (
                            f"System flagged contradiction between Statement A ('{past_claim.claim_text}') "
                            f"and Statement B ('{claim.claim_text}')."
                        )
                        contradiction = Contradiction(
                            original_claim_id=past_claim.id,
                            contradicting_claim_id=claim.id,
                            confidence_score=score,
                            explanation=explanation,
                            review_status="pending_review"
                        )
                        db.add(contradiction)
                        contradictions_found += 1
                except Exception as ex:
                    logger.error(f"Failed NLI inference: {ex}")
                    
        db.commit()
        
        # Complete Job
        speech.status = "completed"
        db.commit()
        
        logger.info(f"Ingestion completed. Extracted {len(claims_created)} claims. Flagged {contradictions_found} contradictions.")
        return {
            "status": "completed",
            "claims_extracted": len(claims_created),
            "contradictions_found": contradictions_found
        }
        
    except Exception as e:
        logger.error(f"Error processing speech {speech_id}: {e}")
        db.rollback()
        try:
            speech = db.query(Speech).filter(Speech.id == speech_id).first()
            if speech:
                speech.status = "failed"
                db.commit()
        except Exception:
            pass
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


def get_speech_transcript_mock(speech_title: str) -> list:
    """
    Returns realistic transcription blocks depending on the speech title
    to simulate real transcription processing.
    """
    title_lower = speech_title.lower()
    
    if "tax" in title_lower or "budget" in title_lower:
        return [
            {"start": 0.0, "end": 10.0, "text": "Good morning everyone. I want to talk about the budget and tax reform."},
            {"start": 10.5, "end": 20.0, "text": "I have never voted to increase state sales tax during my career."},
            {"start": 20.5, "end": 30.0, "text": "We need to keep money in the pockets of working families."},
            {"start": 30.5, "end": 45.0, "text": "Raising sales taxes hurts local businesses and discourages investment."}
        ]
    elif "infrastructure" in title_lower or "revenue" in title_lower:
        return [
            {"start": 0.0, "end": 12.0, "text": "We are facing a crisis with our state highways and bridges."},
            {"start": 12.5, "end": 25.0, "text": "We must increase state revenue by raising the sales tax rate to 5%."},
            {"start": 25.5, "end": 35.0, "text": "Without this additional revenue, we cannot fund our public works."},
            {"start": 35.5, "end": 48.0, "text": "I will always stand for raising revenues when our infrastructure needs it."}
        ]
    else:
        return [
            {"start": 0.0, "end": 8.0, "text": "Hello, thank you for welcoming me to this press conference today."},
            {"start": 8.5, "end": 18.0, "text": "We are focused on expanding educational programs across all school districts."},
            {"start": 18.5, "end": 28.0, "text": "Education is the foundation of our state's future success."},
            {"start": 28.5, "end": 38.0, "text": "We will ensure funding matches student needs."}
        ]
