"""Isolated 12Axes research API.

Default: read-only methodological preview. Human political answers are NEVER
collected unless an independently approved, SHA-pinned study is configured.
Deploy independently from the public 12Axes scoring API.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets

from fastapi import FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from research.assignment import DEFAULT_INSTRUMENT, generate_form, load_instrument

app = FastAPI(title="12Axes Research API", version="0.1.0", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in
                   os.getenv("RESEARCH_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
                   if origin.strip() and origin.strip() != "*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

CHOICES = frozenset({
    "STRONGLY_AGREE", "AGREE", "NEUTRAL", "DISAGREE", "STRONGLY_DISAGREE"
})


class ConsentRequest(BaseModel):
    consent: bool
    age_18_plus: bool
    consent_version: str = Field(min_length=1, max_length=32)
    invite_code: str = Field(min_length=1, max_length=256)


class ResponseRequest(BaseModel):
    answers: dict[str, str]
    archetype: dict[str, str] = Field(default_factory=dict)


def _instrument():
    path = Path(os.getenv("RESEARCH_INSTRUMENT_PATH", str(DEFAULT_INSTRUMENT)))
    return load_instrument(path)


def _fielding_settings(*, require_collection: bool = False) -> tuple[dict, str, str]:
    """Only allow explicitly approved and immutable study instruments."""
    if require_collection and os.getenv("RESEARCH_COLLECTION_ENABLED", "").lower() != "true":
        raise HTTPException(503, "Study collection is disabled")
    settings = ["RESEARCH_DATABASE_URL", "RESEARCH_STUDY_SEED", "RESEARCH_TOKEN_PEPPER",
                "RESEARCH_INVITE_CODE", "RESEARCH_APPROVED_VERSION",
                "RESEARCH_INSTRUMENT_SHA256", "RESEARCH_ETHICS_REFERENCE",
                "RESEARCH_CONSENT_VERSION"]
    missing = [name for name in settings if not os.getenv(name)]
    if missing:
        raise HTTPException(503, "Study configuration is incomplete")
    pepper = os.environ["RESEARCH_TOKEN_PEPPER"]
    seed = os.environ["RESEARCH_STUDY_SEED"]
    if len(pepper) < 32 or len(seed) < 32 or len(os.environ["RESEARCH_INVITE_CODE"]) < 16:
        raise HTTPException(503, "Study secrets are too short")
    instrument_path = Path(os.getenv("RESEARCH_INSTRUMENT_PATH", str(DEFAULT_INSTRUMENT)))
    raw = instrument_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    instrument = load_instrument(instrument_path)
    if (instrument["instrument_version"] != os.environ["RESEARCH_APPROVED_VERSION"]
        or instrument.get("research_status") != "APPROVED_FOR_FIELDING"
        or not hmac.compare_digest(digest, os.environ["RESEARCH_INSTRUMENT_SHA256"])
        or instrument["instrument_version"].startswith("draft")):
        raise HTTPException(503, "An approved, SHA-pinned non-draft instrument is required")
    return instrument, pepper, seed


def _connect():
    """No DB connection exists in preview mode. Requires dedicated PostgreSQL."""
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError:
        raise HTTPException(503, "Research PostgreSQL driver is not installed")
    return psycopg.connect(os.environ["RESEARCH_DATABASE_URL"], row_factory=dict_row,
                           connect_timeout=5)


def _hash_token(token: str, pepper: str) -> str:
    return hmac.new(pepper.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


def _auth_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "A participant access token is required")
    token = authorization[7:]
    if len(token) != 64 or any(ch not in "0123456789abcdef" for ch in token):
        raise HTTPException(401, "Invalid participant access token")
    return token


def _make_form(instrument: dict, index: int, seed: str, lang: str) -> dict:
    if lang not in ("pt", "en"):
        raise HTTPException(400, "Unsupported locale")
    allocation = generate_form(index, instrument, study_seed=seed)
    by_id = {item["id"]: item for item in instrument["items"]}
    return {
        "instrument_version": allocation["instrument_version"],
        "form_index": allocation["form_index"],
        "language": lang,
        "questions": [
            {"id": qid, "axis_id": by_id[qid]["axis_id"],
             "text": by_id[qid]["wording"][lang]} for qid in allocation["question_ids"]
        ],
        "archetype_questions": [
            {"id": item["id"], "text": item["text"][lang],
             "options": [{"id": o["id"], "text": o["text"][lang]} for o in item["options"]]}
            for item in instrument["archetype_questions"]
        ],
        "choices": sorted(CHOICES),
        "notice": "Draft preview only; no responses are saved." if instrument["instrument_version"].startswith("draft")
                  else "Only consented study sessions may submit responses."
    }


def validate_responses(instrument: dict, assigned_ids: list[str],
                       answers: dict[str, str], archetype: dict[str, str]) -> None:
    """Strictly reject extraneous, missing, or malformed data."""
    if set(answers) != set(assigned_ids) or len(assigned_ids) != 120:
        raise ValueError("Exactly the 120 assigned questions must be answered")
    if any(value not in CHOICES for value in answers.values()):
        raise ValueError("Invalid Likert response")
    archetype_questions = {item["id"]: {o["id"] for o in item["options"]}
                           for item in instrument["archetype_questions"]}
    if set(archetype) != set(archetype_questions):
        raise ValueError("All five archetype questions must be answered")
    if any(value not in archetype_questions[key] for key, value in archetype.items()):
        raise ValueError("Invalid archetype response")


@app.get("/research-api/health")
def health():
    return {"status": "ok", "collection_enabled": False if
            os.getenv("RESEARCH_COLLECTION_ENABLED", "").lower() != "true" else "requires_verified_configuration"}


@app.get("/research-api/preview")
def preview(form_index: int = Query(0, ge=0, le=100000), lang: str = "en"):
    # This endpoint is safe in draft mode: allocation only; no DB, no consent or storage.
    return _make_form(_instrument(), form_index, "draft-only", lang)


@app.post("/research-api/sessions", status_code=status.HTTP_201_CREATED)
def create_session(request: ConsentRequest, lang: str = "en"):
    instrument, pepper, seed = _fielding_settings(require_collection=True)
    if not request.consent or not request.age_18_plus:
        raise HTTPException(400, "Explicit research consent and adult eligibility required")
    if not hmac.compare_digest(request.consent_version, os.environ["RESEARCH_CONSENT_VERSION"]):
        raise HTTPException(400, "Consent document version mismatch")
    if not hmac.compare_digest(request.invite_code, os.environ["RESEARCH_INVITE_CODE"]):
        raise HTTPException(403, "Invalid study invitation")
    if lang not in ("pt", "en"):
        raise HTTPException(400, "Unsupported locale")
    token = secrets.token_hex(32)
    token_hash = _hash_token(token, pepper)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT nextval('research_form_index_seq') - 1 AS idx")
            index = cur.fetchone()["idx"]
            allocation = generate_form(index, instrument, study_seed=seed)
            cur.execute(
                """INSERT INTO research_sessions
                    (token_hash, instrument_version, consent_version, ethics_reference,
                     form_index, language, assigned_ids)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (token_hash, instrument["instrument_version"], request.consent_version,
                 os.environ["RESEARCH_ETHICS_REFERENCE"], index, lang,
                 allocation["question_ids"]),
            )
    return {"participant_token": token, "form": _make_form(instrument, index, seed, lang),
            "withdrawal_instructions": "Keep your access token to withdraw. No email or account is collected."}


def _active_session(token_hash: str):
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT instrument_version, form_index, language, assigned_ids,
                                  completed_at FROM research_sessions
                           WHERE token_hash=%s AND expires_at > now()""", (token_hash,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Session missing, expired or withdrawn")
    return row


@app.get("/research-api/session")
def get_session(authorization: str | None = Header(None)):
    instrument, pepper, seed = _fielding_settings()
    row = _active_session(_hash_token(_auth_token(authorization), pepper))
    if row["instrument_version"] != instrument["instrument_version"]:
        raise HTTPException(409, "Instrument version changed; contact research administrator")
    return {"form": _make_form(instrument, row["form_index"], seed, row["language"]),
            "submitted": row["completed_at"] is not None}


@app.post("/research-api/responses", status_code=status.HTTP_204_NO_CONTENT)
def submit_responses(request: ResponseRequest, authorization: str | None = Header(None)):
    instrument, pepper, _ = _fielding_settings(require_collection=True)
    token_hash = _hash_token(_auth_token(authorization), pepper)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT instrument_version, assigned_ids, completed_at
                           FROM research_sessions
                           WHERE token_hash=%s AND expires_at > now() FOR UPDATE""",
                        (token_hash,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Session missing, expired or withdrawn")
            if row["instrument_version"] != instrument["instrument_version"]:
                raise HTTPException(409, "Instrument version mismatch")
            if row["completed_at"] is not None:
                raise HTTPException(409, "Session was already completed")
            try:
                validate_responses(instrument, row["assigned_ids"], request.answers, request.archetype)
            except ValueError as exc:
                raise HTTPException(422, str(exc))
            cur.execute("""UPDATE research_sessions
                           SET answers=%s::jsonb, archetype_answers=%s::jsonb, completed_at=now()
                           WHERE token_hash=%s""",
                        (json.dumps(request.answers), json.dumps(request.archetype), token_hash))
    return None


@app.post("/research-api/withdraw", status_code=status.HTTP_204_NO_CONTENT)
def withdraw(authorization: str | None = Header(None)):
    _, pepper, _ = _fielding_settings()
    token_hash = _hash_token(_auth_token(authorization), pepper)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM research_sessions WHERE token_hash=%s", (token_hash,))
    return None
