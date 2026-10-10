"""Offline deterministic assignment invariants; run: python3 -m unittest discover -s research/tests."""
import copy
import unittest
from collections import Counter

from research.assignment import coverage_report, generate_form, load_instrument, validate_instrument


class ResearchAssignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.instrument = load_instrument()
        cls.lookup = {item["id"]: item for item in cls.instrument["items"]}

    def test_survey_stays_unapproved_for_fielding(self):
        self.assertEqual(self.instrument["research_status"], "NOT_APPROVED_FOR_FIELDING")

    def test_common_core_and_rotating_items_have_expected_counts(self):
        form = generate_form(1, self.instrument)
        self.assertEqual(len(form["question_ids"]), 120)
        self.assertEqual(len(set(form["question_ids"])), 120)
        self.assertEqual(len(form["common_item_ids"]), 72)
        self.assertEqual(len(form["rotated_item_ids"]), 48)
        self.assertFalse(set(form["common_item_ids"]) & set(form["rotated_item_ids"]))
        counts = Counter((self.lookup[q]["axis_id"], self.lookup[q]["agree_pole"])
                         for q in form["question_ids"])
        for axis in self.instrument["axes"]:
            for pole in ("LEFT", "RIGHT"):
                self.assertEqual(counts[(axis["id"], pole)], 5)

    def test_same_index_and_seed_reproduces_exact_form(self):
        first = generate_form(73, self.instrument, study_seed="study-alpha")
        second = generate_form(73, self.instrument, study_seed="study-alpha")
        self.assertEqual(first, second)
        self.assertNotEqual(first["question_ids"],
                            generate_form(74, self.instrument, study_seed="study-alpha")["question_ids"])

    def test_each_rotating_item_appears_twice_per_seven_forms(self):
        core = set(self.instrument["assignment"]["common_ids"])
        for start in (0, 7, 14):
            hits = Counter()
            for idx in range(start, start + 7):
                hits.update(generate_form(idx, self.instrument)["rotated_item_ids"])
            self.assertEqual(len(hits), 168)
            self.assertEqual(set(hits.values()), {2})
            self.assertFalse(core & set(hits))

    def test_coverage_invariants(self):
        stats = coverage_report(self.instrument, 14)
        self.assertEqual(stats["common_min"], 14)
        self.assertEqual(stats["common_max"], 14)
        self.assertEqual(stats["rotated_min"], 4)
        self.assertEqual(stats["rotated_max"], 4)
        self.assertEqual(stats["total_answer_slots"], 14 * 120)

    def test_rejects_duplicated_core_items(self):
        broken = copy.deepcopy(self.instrument)
        broken["assignment"]["common_ids"][0] = broken["assignment"]["common_ids"][1]
        with self.assertRaises(ValueError):
            validate_instrument(broken)

    def test_rejects_polarity_corruption(self):
        broken = copy.deepcopy(self.instrument)
        broken["items"][0]["agree_pole"] = "INVALID"
        with self.assertRaises(ValueError):
            validate_instrument(broken)

    def test_rejects_invalid_indices(self):
        with self.assertRaises(ValueError):
            generate_form(-1, self.instrument)
        with self.assertRaises(ValueError):
            generate_form(True, self.instrument)


if __name__ == "__main__":
    unittest.main()
