"""Offline phase-two methodological tooling tests with *synthetic expert ratings*."""
from __future__ import annotations
from collections import Counter
import csv
from pathlib import Path
import tempfile
import unittest

from research.content_review import COLUMNS, make_packet, parse_reviews, summarize_reviews, verify_snapshot, write_packet
from research.cognitive_packets import make_interview_packet, audit_packet_rotation


class Phase2ContentValidationTests(unittest.TestCase):
    def test_locked_snapshot_and_all_240_items(self):
        self.assertEqual(len(verify_snapshot()), 40)
        for locale in ("en","pt"):
            rows = make_packet("expert_01",locale)
            self.assertEqual(len(rows), 240)
            self.assertEqual(len(set(row["item_id"] for row in rows)), 240)
            self.assertEqual(sum(row["is_common_item"] == "yes" for row in rows),72)
            self.assertTrue(all(row["relevance_1to4"] == "" for row in rows))

    def test_empty_packet_is_not_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.csv"
            write_packet(path, "expert_01", "en")
            scored = parse_reviews([path])
            self.assertEqual(scored, [])
            report = summarize_reviews(scored)
            self.assertEqual(report["reviewed_ratings"], 0)
            self.assertEqual(report["coverage"]["en"]["items_with_any_review"], 0)
            self.assertIsNone(report["coverage"]["en"]["s_cvi_ave_expert_reviewed_only"])

    def test_independent_graded_reviews_and_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for rid, grade in (("rev_a","4"),("rev_b","2")):
                path = Path(directory) / f"{rid}.csv"
                rows = make_packet(rid,"en")
                row = rows[0]
                for metric in ("relevance_1to4","clarity_1to4","construct_fit_1to4"):
                    row[metric] = grade
                row["leading_yes_no"] = "yes" if rid == "rev_b" else "no"
                row["proposed_action"] = "revise" if rid == "rev_b" else "retain"
                with path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle,fieldnames=COLUMNS)
                    writer.writeheader();writer.writerows(rows)
                paths.append(path)
            ratings = parse_reviews(paths)
            report = summarize_reviews(ratings,min_raters=2)
            result = report["items"][0]
            self.assertEqual(len(ratings),2)
            self.assertEqual(result["i_cvi_relevance"],0.5)
            self.assertEqual(result["risk_yes_counts"]["leading_yes_no"],1)
            self.assertTrue(result["requires_discussion"])
            self.assertIsNone(report["coverage"]["en"]["s_cvi_ave_expert_reviewed_only"])
            with self.assertRaises(ValueError):
                parse_reviews(paths + [paths[0]])

    def test_invalid_or_modified_question_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "broken.csv"
            rows = make_packet("rev_1","pt")
            rows[0]["question_text"] = "Modified without new version"
            with file.open("w",encoding="utf-8",newline="") as handle:
                writer=csv.DictWriter(handle,fieldnames=COLUMNS)
                writer.writeheader();writer.writerows(rows)
            with self.assertRaises(ValueError):
                parse_reviews([file])

    def test_twenty_packet_rotation_covers_each_item_twice(self):
        audit = audit_packet_rotation()
        self.assertEqual(audit["unique_items_covered"],240)
        self.assertEqual(audit["appearances_per_item"],2)
        packet = make_interview_packet(3,language="pt")
        self.assertEqual(len(packet),24)
        self.assertEqual(len({x["item_id"] for x in packet}),24)
        self.assertEqual(len({x["axis_id"] for x in packet}),12)
        self.assertEqual(set(Counter(x["agree_pole"] for x in packet).values()),{12})
        self.assertIn("suas palavras",packet[0]["probe_1"])
        self.assertEqual(packet,make_interview_packet(3,language="pt"))
        with self.assertRaises(ValueError):
            make_interview_packet(20)
