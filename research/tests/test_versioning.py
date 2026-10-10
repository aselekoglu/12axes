"""Ensure approved-study format can be frozen without making the draft collectable."""
import copy
import unittest

from research.assignment import load_instrument, validate_instrument


class VersioningTests(unittest.TestCase):
    def test_draft_is_research_preview_only(self):
        data = load_instrument()
        self.assertEqual(data["research_status"], "NOT_APPROVED_FOR_FIELDING")

    def test_pilot_requires_approved_status(self):
        data = copy.deepcopy(load_instrument())
        data["instrument_version"] = "pilot-1.0"
        with self.assertRaises(ValueError):
            validate_instrument(data)
        data["research_status"] = "APPROVED_FOR_FIELDING"
        validate_instrument(data)

    def test_wrong_status_on_draft_rejected(self):
        data = copy.deepcopy(load_instrument())
        data["research_status"] = "APPROVED_FOR_FIELDING"
        with self.assertRaises(ValueError):
            validate_instrument(data)

    def test_unknown_versions_rejected(self):
        data = copy.deepcopy(load_instrument())
        data["instrument_version"] = "draft-0.2"
        with self.assertRaises(ValueError):
            validate_instrument(data)


if __name__ == "__main__":
    unittest.main()
