"""Stdlib unittest for agent.tools — ls / cat / grep, with safety checks."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent.tools import ls, cat, grep, MAX_CAT_BYTES


class TestLs(unittest.TestCase):
    def test_lists_visible_entries_with_trailing_slash_for_dirs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a.txt").write_text("")
            (root / "sub").mkdir()
            (root / ".hidden").write_text("")
            self.assertEqual(ls(".", root=root), ["a.txt", "sub/"])

    def test_raises_on_missing_path(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                ls("nope", root=Path(d))

    def test_refuses_escape(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                ls("..", root=Path(d))


class TestCat(unittest.TestCase):
    def test_reads_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a.txt").write_text("hello world")
            self.assertEqual(cat("a.txt", root=root), "hello world")

    def test_truncates_large_files(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            big = "x" * (MAX_CAT_BYTES + 1000)
            (root / "big.txt").write_text(big)
            out = cat("big.txt", root=root)
            self.assertTrue(out.startswith("x" * 100))
            self.assertIn("truncated", out)
            self.assertLessEqual(len(out), MAX_CAT_BYTES + 200)

    def test_refuses_escape(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                cat("../outside", root=Path(d))

    def test_raises_on_directory(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                cat(".", root=Path(d))


class TestGrep(unittest.TestCase):
    def test_finds_matches_in_single_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a.txt").write_text("alpha\nbeta\nalphabeta\n")
            out = grep("alpha", "a.txt", root=root)
            self.assertEqual(len(out), 2)
            self.assertIn("a.txt:1", out[0])
            self.assertIn("a.txt:3", out[1])

    def test_finds_matches_recursively(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a.txt").write_text("hit here\n")
            (root / "sub").mkdir()
            (root / "sub" / "b.txt").write_text("also hit\n")
            out = grep("hit", ".", root=root)
            self.assertEqual(len(out), 2)

    def test_respects_max_matches(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a.txt").write_text("hit\n" * 100)
            out = grep("hit", "a.txt", root=root, max_matches=5)
            self.assertEqual(len(out), 5)

    def test_refuses_escape(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                grep("x", "../escape", root=Path(d))


if __name__ == "__main__":
    unittest.main()
