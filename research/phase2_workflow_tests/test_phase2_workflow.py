"""Phase 2 pipelines: synthetic fixtures are not actual human evidence."""
from __future__ import annotations
import csv
from pathlib import Path
import tempfile
import unittest

from research.item_audit import audit_bank
from research.cognitive_review import make_template,load_interviews,summarize_interviews,FIELDS
from research.phase2_workflow import decision_template,validate_decisions,readiness,COLUMNS


class TestPhase2Workflow(unittest.TestCase):
    def test_audit_source_and_no_inferred_content_validity(self):
        report=audit_bank()
        self.assertEqual(report["items"],240)
        self.assertEqual(report["language_item_rows"],480)
        self.assertEqual(report["core_items"],72)
        self.assertEqual(len(report["axis_polarity"]),24)
        self.assertEqual(set(report["axis_polarity"].values()),{10})
        self.assertTrue(report["locked_git_blob_sha"])
        self.assertNotIn("scientific_validity",report)

    def test_empty_research_gates_fail_closed(self):
        report=readiness()
        self.assertFalse(report["can_collect_human_political_opinions"])
        self.assertFalse(report["gates"]["expert_en_240_complete"])
        self.assertFalse(report["gates"]["cognitive_pt_240_observed_twice"])
        self.assertEqual(report["editorial"]["recorded"],0)
        self.assertEqual(report["editorial"]["missing"],480)
        self.assertTrue(report["gates"]["locked_draft_intact"])

    def test_decision_template_creates_exact_pending_480(self):
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/"decisions.csv"
            decision_template(dest)
            with dest.open() as f:
                records=list(csv.DictReader(f))
            self.assertEqual(len(records),480)
            self.assertEqual({r["language"] for r in records},{"en","pt"})
            self.assertEqual(validate_decisions(dest),[])
            with self.assertRaises(FileExistsError):
                decision_template(dest)

    def test_fabricated_editorial_decision_without_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/"ledger.csv"
            decision_template(dest)
            with dest.open() as f: rows=list(csv.DictReader(f))
            rows[0]["decision"]="retain"
            with dest.open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=COLUMNS);w.writeheader();w.writerows(rows)
            with self.assertRaises(ValueError):
                validate_decisions(dest)
            rows[0].update({"expert_evidence_refs":"SYNTHETIC_FIXTURE",
                            "rationale":"Test fixture only",
                            "editor_code":"test_editor","decision_date":"2026-10-10"})
            with dest.open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=COLUMNS);w.writeheader();w.writerows(rows)
            self.assertEqual(len(validate_decisions(dest)),1)
            report=readiness(decisions=dest)
            self.assertFalse(report["can_collect_human_political_opinions"])

    def test_blank_interview_not_counted_and_coded_probe_checked(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"interview.csv"
            make_template(target,"COGTEST_01",0,"en")
            self.assertEqual(load_interviews([target]),[])
            with target.open() as f: rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),24)
            rows[0].update({"comprehension":"issue_observed",
                            "retrieval":"not_assessed","judgment":"not_observed",
                            "response_mapping":"not_observed","severity":"moderate",
                            "observation":"SYNTHETIC test observation","suggested_action":"discuss"})
            with target.open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
            received=load_interviews([target])
            self.assertEqual(len(received),1)
            summary=summarize_interviews(received)
            self.assertEqual(summary["by_language"]["en"]["items_with_issues"],1)
            self.assertEqual(summary["by_language"]["en"]["items_observed_twice"],0)
            with self.assertRaises(ValueError):
                load_interviews([target,target])

    def test_interview_cannot_invent_unassigned_item(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"interview.csv"
            make_template(target,"COGTEST_02",2,"pt")
            with target.open() as f: rows=list(csv.DictReader(f))
            rows[0]["item_id"]="fake_01"
            with target.open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
            with self.assertRaises(ValueError):
                load_interviews([target])


if __name__=="__main__":unittest.main()
