"""Research API and form validation: no real participant data or DB involved."""
import copy
import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from research.assignment import load_instrument, generate_form
from research.service import app, _fielding_settings, _hash_token, validate_responses


class ResearchApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.instrument = load_instrument()

    def test_preview_does_not_create_a_session(self):
        res = self.client.get("/research-api/preview?form_index=3&lang=en")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data["questions"]), 120)
        self.assertEqual(len(data["archetype_questions"]), 5)
        self.assertIn("no responses are saved", data["notice"])

    def test_bad_locale_rejected(self):
        res = self.client.get("/research-api/preview?lang=de")
        self.assertEqual(res.status_code, 400)

    def test_collection_disabled_by_default(self):
        with patch.dict(os.environ, {"RESEARCH_COLLECTION_ENABLED": "false"}):
            res = self.client.post("/research-api/sessions", json={
                "consent": True, "age_18_plus": True,
                "consent_version": "v1", "invite_code": "test-code"
            })
        self.assertEqual(res.status_code, 503)

    def test_draft_cannot_be_enabled_even_when_secrets_present(self):
        names = {
            "RESEARCH_COLLECTION_ENABLED": "true",
            "RESEARCH_DATABASE_URL": "postgresql://unused",
            "RESEARCH_STUDY_SEED": "a" * 32,
            "RESEARCH_TOKEN_PEPPER": "b" * 32,
            "RESEARCH_INVITE_CODE": "c" * 16,
            "RESEARCH_APPROVED_VERSION": "draft-0.1",
            "RESEARCH_INSTRUMENT_SHA256": "0" * 64,
            "RESEARCH_ETHICS_REFERENCE": "NOT_REAL",
            "RESEARCH_CONSENT_VERSION": "v1",
        }
        with patch.dict(os.environ, names):
            with self.assertRaises(HTTPException) as ctx:
                _fielding_settings()
        self.assertEqual(ctx.exception.status_code, 503)

    def test_strict_complete_responses_validation(self):
        ids = generate_form(0, self.instrument)["question_ids"]
        answers = {qid: "NEUTRAL" for qid in ids}
        archetypes = {q["id"]: q["options"][0]["id"]
                      for q in self.instrument["archetype_questions"]}
        validate_responses(self.instrument, ids, answers, archetypes)
        invalid = copy.deepcopy(answers)
        invalid["unassigned_999"] = "NEUTRAL"
        with self.assertRaises(ValueError):
            validate_responses(self.instrument, ids, invalid, archetypes)
        invalid = copy.deepcopy(answers)
        invalid[ids[0]] = "NOT_APPLICABLE"
        with self.assertRaises(ValueError):
            validate_responses(self.instrument, ids, invalid, archetypes)
        with self.assertRaises(ValueError):
            validate_responses(self.instrument, ids, answers, {})

    def test_token_hash_is_keyed_and_irreversible(self):
        self.assertNotEqual(_hash_token("x", "a" * 32), _hash_token("x", "b" * 32))


if __name__ == "__main__":
    unittest.main()
