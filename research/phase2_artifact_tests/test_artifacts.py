"""No external participants/reviewers. Test only locked draft and false approval states."""
import tempfile
from pathlib import Path
import unittest

from research.item_dashboard import build_dashboard
from research.phase2_candidate import compile_candidate
from research.phase2_workflow import decision_template


class Phase2ArtifactsTest(unittest.TestCase):
    def test_static_dashboard_contains_240_questions_two_languages_and_no_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"audit.html"
            result=build_dashboard(dest)
            page=dest.read_text()
            self.assertEqual(result["items"],240)
            self.assertEqual(result["languages"],2)
            self.assertIn("NOT VALIDATED",page)
            self.assertIn("estrutura_01",page)
            self.assertIn("Português",page)
            self.assertNotIn("<script src=",page)
            self.assertNotIn("http://",page)
            self.assertNotIn("https://",page)
            self.assertNotIn("fetch(",page)
            with self.assertRaises(FileExistsError):
                build_dashboard(dest)

    def test_cannot_emit_candidate_without_external_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            decisions=folder/"decisions.csv"
            decision_template(decisions)
            output=folder/"candidate.json"
            with self.assertRaises(ValueError):
                compile_candidate(decisions,[],[],output)
            self.assertFalse(output.exists())


if __name__=="__main__":unittest.main()
