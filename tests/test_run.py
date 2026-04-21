"""Stdlib unittest for agent.run — the day-3 dry-run harness."""
from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agent import run


class TestRunMain(unittest.TestCase):
    def test_dry_run_with_mock_prints_proposal(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = run.main(["--mock"])
        self.assertEqual(rc, 0)
        output = buf.getvalue()
        self.assertIn("PROPOSED CHANGE", output)
        self.assertIn("WHY", output)
        self.assertIn("dry run", output)

    def test_save_writes_file(self):
        with tempfile.TemporaryDirectory() as d:
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = run.main(["--mock", "--save", d])
            self.assertEqual(rc, 0)

            saved = list(Path(d).glob("proposal-*.md"))
            self.assertEqual(len(saved), 1, f"expected one proposal file, got {saved}")

            body = saved[0].read_text()
            self.assertIn("# Proposal", body)
            self.assertIn("**Change:**", body)
            self.assertIn("## WHY", body)


if __name__ == "__main__":
    unittest.main()
