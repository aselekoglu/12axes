import csv
from pathlib import Path
import tempfile
import unittest

from research.analysis.synthetic import simulate


class SyntheticSmokeTests(unittest.TestCase):
    def test_only_explicitly_marked_fake_data_written(self):
        with tempfile.TemporaryDirectory() as work:
            folder = Path(work) / "fake"
            stats = simulate(folder, participants=14, seed=42, completion=1.0)
            self.assertEqual(stats["assigned_rows"], 14 * 120)
            self.assertEqual(stats["answer_rows"], 14 * 120)
            self.assertTrue((folder / "SYNTHETIC_TEST_DATA_ONLY").exists())
            with (folder / "participants.csv").open() as stream:
                participants = list(csv.DictReader(stream))
            self.assertEqual(len(participants), 14)
            self.assertEqual({(p["language"], p["split"]) for p in participants},
                             {("en", "efa"), ("en", "cfa"), ("pt", "efa"), ("pt", "cfa")})
            self.assertTrue(all(row["participant_id"].startswith("FAKE_SYNTHETIC_")
                                for row in participants))
            with self.assertRaises(FileExistsError):
                simulate(folder, participants=14)

    def test_incomplete_sessions_have_assignments_but_no_answers(self):
        with tempfile.TemporaryDirectory() as work:
            stats = simulate(Path(work) / "not_done", participants=7, completion=0)
            self.assertEqual(stats["assigned_rows"], 7 * 120)
            self.assertEqual(stats["answer_rows"], 0)


if __name__ == "__main__":
    unittest.main()
