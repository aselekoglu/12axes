import copy
import unittest

from research.expert_audit import summarize_audit, validate_audit


def document():
    def row(rater, ans):
        return {
            "rater_id": rater, "question_id": "economia_01",
            "axis_id": "economia", "evidence_state": "OBSERVED", "answer": ans,
            "sources": [{"url": "https://example.org/archive/123",
                         "date": "1945-01-01", "note": "Contemporaneous statement"}]
        }
    return {
        "profile_id": "sample-not-a-real-figure",
        "reference_period": "1940–1950", "instrument_version": "draft-0.1",
        "ratings": [row("expert-a", "D"), row("expert-b", "C")]
    }


class EvidenceAuditTests(unittest.TestCase):
    def test_disagreement_is_not_suppressed(self):
        result = summarize_audit(document())
        self.assertEqual(result["items_with_multiple_raters"], 1)
        self.assertEqual(result["items_with_exact_agreement"], 0)
        self.assertEqual(result["items_with_disagreement"], ["economia_01"])

    def test_missing_views_not_neutral(self):
        data = document()
        data["ratings"][0].update({"evidence_state": "UNKNOWN", "answer": "N"})
        with self.assertRaises(ValueError):
            validate_audit(data)
        data["ratings"][0]["answer"] = None
        validate_audit(data)

    def test_observation_requires_source(self):
        data = document()
        data["ratings"][0]["sources"] = []
        with self.assertRaises(ValueError):
            validate_audit(data)

    def test_duplicate_rater_question_rejected(self):
        data = document()
        data["ratings"].append(copy.deepcopy(data["ratings"][0]))
        with self.assertRaises(ValueError):
            validate_audit(data)

    def test_insecure_source_rejected(self):
        data = document()
        data["ratings"][0]["sources"][0]["url"] = "http://example.org/archive"
        with self.assertRaises(ValueError):
            validate_audit(data)


if __name__ == "__main__":
    unittest.main()
