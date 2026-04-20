"""Stdlib unittest for agent.driver — parsing, state reading, and end-to-end mock."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent.driver import parse, read_state, propose_next_change, _mock_model


class TestParse(unittest.TestCase):
    def test_parses_well_formed_response(self):
        resp = (
            "PROPOSAL: add a CHANGELOG.md.\n"
            "WHY:\n"
            "Because it's useful.\n"
            "Multi-line bodies are fine."
        )
        p = parse(resp)
        self.assertEqual(p.change_description, "add a CHANGELOG.md.")
        self.assertIn("useful", p.why_entry)
        self.assertIn("Multi-line", p.why_entry)

    def test_handles_inline_why_content(self):
        resp = "PROPOSAL: rename foo to bar.\nWHY: one-line justification."
        p = parse(resp)
        self.assertEqual(p.change_description, "rename foo to bar.")
        self.assertEqual(p.why_entry, "one-line justification.")

    def test_missing_sections_yield_empty_strings(self):
        p = parse("nothing structured here")
        self.assertEqual(p.change_description, "")
        self.assertEqual(p.why_entry, "")


class TestReadState(unittest.TestCase):
    def test_includes_present_files_and_tree(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "WHY.md").write_text("why content")
            (root / "ROADMAP.md").write_text("roadmap content")
            (root / "extra.txt").write_text("extra")

            state = read_state(root)

            self.assertIn("WHY.md", state)
            self.assertIn("why content", state)
            self.assertIn("ROADMAP.md", state)
            self.assertIn("extra.txt", state)

    def test_missing_files_are_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            state = read_state(Path(d))
            # no WHY/ROADMAP but FILE TREE section must still be present
            self.assertIn("FILE TREE", state)


class TestProposeWithMock(unittest.TestCase):
    def test_mock_produces_parseable_proposal(self):
        with tempfile.TemporaryDirectory() as d:
            p = propose_next_change(_mock_model, root=Path(d))
            self.assertTrue(p.change_description)
            self.assertTrue(p.why_entry)


if __name__ == "__main__":
    unittest.main()
