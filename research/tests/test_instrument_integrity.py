"""Enforce exact snapshot bytes for versioned, non-fielded draft instruments."""
import hashlib
import json
import unittest
from pathlib import Path

from research.assignment import DEFAULT_INSTRUMENT, load_instrument


class InstrumentIntegrityTests(unittest.TestCase):
    def test_snapshot_is_locked_by_git_blob_hash(self):
        lock_path = DEFAULT_INSTRUMENT.parent / "LOCK.json"
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        raw = DEFAULT_INSTRUMENT.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        self.assertEqual(actual, lock["snapshot_git_blob_sha"])
        self.assertEqual(load_instrument()["instrument_version"], lock["instrument_version"])

    def test_no_person_data_or_active_fielding_flag(self):
        document = load_instrument()
        self.assertEqual(document["research_status"], "NOT_APPROVED_FOR_FIELDING")
        self.assertNotIn("participants", document)
        self.assertNotIn("responses", document)


if __name__ == "__main__":
    unittest.main()
