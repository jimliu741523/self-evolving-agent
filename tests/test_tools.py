"""Stdlib unittest for agent.tools — ls / cat / grep, with safety checks."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent.tools import (
    ls, cat, grep, write_file, run_command,
    MAX_CAT_BYTES, MAX_WRITE_BYTES, EXEC_ALLOWLIST,
)


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


class TestWriteFile(unittest.TestCase):
    def test_writes_and_creates_parents(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            p = write_file("notes/x.md", "hello\n", root=root)
            self.assertTrue(p.exists())
            self.assertEqual(p.read_text(), "hello\n")

    def test_refuses_escape(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                write_file("../escape.txt", "x", root=Path(d))

    def test_refuses_t1_locked_by_default(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for locked in ("agent/driver.py", "POLICY.md", "tests/foo.py", "Makefile"):
                with self.assertRaises(PermissionError, msg=locked):
                    write_file(locked, "x", root=root)

    def test_allow_t1_override_works(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            p = write_file("POLICY.md", "x", allow_t1=True, root=root)
            self.assertEqual(p.read_text(), "x")

    def test_size_cap(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                write_file("big.txt", "x" * (MAX_WRITE_BYTES + 1), root=Path(d))


class TestRunCommand(unittest.TestCase):
    def test_refuses_command_outside_allowlist(self):
        with self.assertRaises(PermissionError):
            run_command("rm")
        with self.assertRaises(PermissionError):
            run_command("/bin/sh")

    def test_python3_echo_runs(self):
        r = run_command("python3", ("-c", "print('hi')"))
        self.assertEqual(r.returncode, 0)
        self.assertIn("hi", r.stdout)
        self.assertFalse(r.timed_out)

    def test_git_only_read_subcommands(self):
        with self.assertRaises(PermissionError):
            run_command("git", ("commit", "-m", "x"))
        with self.assertRaises(PermissionError):
            run_command("git", ("push",))

    def test_git_status_runs(self):
        r = run_command("git", ("status",))
        self.assertEqual(r.returncode, 0)

    def test_timeout_returns_timed_out(self):
        r = run_command(
            "python3",
            ("-c", "import time; time.sleep(5)"),
            timeout=1,
        )
        self.assertTrue(r.timed_out)
        self.assertEqual(r.returncode, -1)

    def test_null_byte_rejected(self):
        with self.assertRaises(ValueError):
            run_command("python3", ("-c\x00", ""))


if __name__ == "__main__":
    unittest.main()
