"""PostgreSQL integration tests using synthetic, non-human responses only.

Never run against real research data: requires loopback + research_test database,
an explicit ephemeral-only acknowledgment and a unique temporary schema.
"""
from __future__ import annotations

import copy
import os
from pathlib import Path
import secrets
import unittest
from unittest.mock import patch
from urllib.parse import urlparse

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from fastapi.testclient import TestClient

from research.assignment import load_instrument
from research import service


class PostgreSQLResearchLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = os.getenv("RESEARCH_TEST_DATABASE_URL", "")
        parsed = urlparse(url)
        if (os.getenv("RESEARCH_INTEGRATION_TEST_ACKNOWLEDGE") != "ephemeral_only"
                or parsed.scheme not in ("postgresql", "postgres")
                or parsed.hostname not in ("localhost", "127.0.0.1")
                or parsed.path != "/research_test"):
            raise unittest.SkipTest("Integration DB must be loopback research_test with explicit acknowledgment")
        cls.url = url
        cls.schema = "ci_" + secrets.token_hex(8)
        cls.mock_pilot = copy.deepcopy(load_instrument())
        cls.mock_pilot["instrument_version"] = "pilot-1.0"
        cls.mock_pilot["research_status"] = "APPROVED_FOR_FIELDING"
        with psycopg.connect(cls.url, autocommit=True) as connection:
            connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(cls.schema)))
        try:
            with cls.connect() as connection:
                ddl = (Path(__file__).resolve().parents[1] / "sql" / "001_sessions.sql").read_text()
                connection.execute(ddl)
        except Exception:
            cls.tearDownClass()
            raise

    @classmethod
    def connect(cls):
        return psycopg.connect(cls.url, row_factory=dict_row, connect_timeout=5,
                               options="-c search_path=" + cls.schema)

    @classmethod
    def tearDownClass(cls):
        if not hasattr(cls, "schema"):
            return
        with psycopg.connect(cls.url, autocommit=True) as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(cls.schema)))

    def test_consent_answer_recovery_duplicate_prevention_and_withdrawal(self):
        env = {
            "RESEARCH_CONSENT_VERSION": "ci-synthetic-v1",
            "RESEARCH_INVITE_CODE": "synthetic-test-invite-only",
            "RESEARCH_COLLECTION_ENABLED": "true",
            "RESEARCH_ETHICS_REFERENCE": "CI_SYNTHETIC_NO_HUMAN_SUBJECTS",
        }
        with (patch.dict(os.environ, env),
              patch("research.service._fielding_settings",
                    return_value=(self.mock_pilot, "integration-only-pepper-" * 3, "ci-study-seed-" * 4)),
              patch("research.service._connect", side_effect=self.connect)):
            client = TestClient(service.app)
            denial = client.post("/research-api/sessions?lang=en", json={
                "consent": False, "age_18_plus": True,
                "consent_version": "ci-synthetic-v1", "invite_code": env["RESEARCH_INVITE_CODE"]
            })
            self.assertEqual(denial.status_code, 400)

            created = client.post("/research-api/sessions?lang=en", json={
                "consent": True, "age_18_plus": True,
                "consent_version": "ci-synthetic-v1", "invite_code": env["RESEARCH_INVITE_CODE"]
            })
            self.assertEqual(created.status_code, 201, created.text)
            payload = created.json()
            token = payload["participant_token"]
            form = payload["form"]
            self.assertEqual(len(form["questions"]), 120)
            self.assertEqual(len({q["id"] for q in form["questions"]}), 120)
            self.assertEqual(len(form["archetype_questions"]), 5)
            auth = {"Authorization": "Bearer " + token}
            before = client.get("/research-api/session", headers=auth)
            self.assertEqual(before.status_code, 200)
            self.assertFalse(before.json()["submitted"])

            answers = {item["id"]: "NEUTRAL" for item in form["questions"]}
            archetypes = {q["id"]: q["options"][0]["id"] for q in form["archetype_questions"]}
            invalid = dict(answers)
            invalid["invented_question"] = "AGREE"
            rejected = client.post("/research-api/responses", headers=auth, json={
                "answers": invalid, "archetype": archetypes
            })
            self.assertEqual(rejected.status_code, 422)
            with self.connect() as conn:
                state = conn.execute("SELECT completed_at FROM research_sessions").fetchone()
            self.assertIsNone(state["completed_at"])

            recorded = client.post("/research-api/responses", headers=auth,
                                   json={"answers": answers, "archetype": archetypes})
            self.assertEqual(recorded.status_code, 204, recorded.text)
            self.assertTrue(client.get("/research-api/session", headers=auth).json()["submitted"])
            repeat = client.post("/research-api/responses", headers=auth,
                                 json={"answers": answers, "archetype": archetypes})
            self.assertEqual(repeat.status_code, 409)
            with self.connect() as conn:
                row = conn.execute("SELECT answers, archetype_answers, assigned_ids "
                                   "FROM research_sessions").fetchone()
            self.assertEqual(row["answers"], answers)
            self.assertEqual(row["archetype_answers"], archetypes)
            self.assertEqual(set(row["assigned_ids"]), set(answers))

            # Withdrawal remains available after new enrollment is switched off.
            os.environ["RESEARCH_COLLECTION_ENABLED"] = "false"
            withdrawn = client.post("/research-api/withdraw", headers=auth)
            self.assertEqual(withdrawn.status_code, 204)
            with self.connect() as conn:
                count = conn.execute("SELECT count(*) AS n FROM research_sessions").fetchone()["n"]
            self.assertEqual(count, 0)
            self.assertEqual(client.get("/research-api/session", headers=auth).status_code, 404)


if __name__ == "__main__":
    unittest.main()
