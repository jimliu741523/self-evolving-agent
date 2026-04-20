"""
agent.tools — read-only inspector tools, day-2.

Three tools the agent can use to ask for targeted file content beyond the
bulk state dump that `driver.read_state` provides:

- `ls(directory)` — list visible entries of a directory inside the repo
- `cat(path)` — read a file (truncated at a byte limit for safety)
- `grep(pattern, path)` — regex search through a file or a subtree

All three refuse to resolve outside the repo root. None of them write
anything.

Day 2 scope intentionally stops here. Writing tools (edit, exec) require
the commit-policy decision, which is day 4 on the roadmap.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Safety caps — kept conservative on purpose.
MAX_CAT_BYTES = 100_000
MAX_GREP_MATCHES = 50


def _safe_path(relative: str, root: Path = REPO_ROOT) -> Path:
    """Resolve a repo-relative path and refuse anything that escapes the root."""
    resolved_root = root.resolve()
    p = (resolved_root / relative).resolve()
    try:
        p.relative_to(resolved_root)
    except ValueError:
        raise ValueError(f"path {relative!r} resolves outside the repo") from None
    return p


def ls(directory: str = ".", root: Path = REPO_ROOT) -> list[str]:
    """List visible (non-dotfile) entries in a directory. Directories get a trailing /."""
    p = _safe_path(directory, root)
    if not p.exists():
        raise FileNotFoundError(str(p))
    if not p.is_dir():
        raise NotADirectoryError(str(p))
    return sorted(
        child.name + ("/" if child.is_dir() else "")
        for child in p.iterdir()
        if not child.name.startswith(".")
    )


def cat(path: str, root: Path = REPO_ROOT, max_bytes: int = MAX_CAT_BYTES) -> str:
    """Read a text file. Truncates at `max_bytes` with a marker, rather than blowing up on large files."""
    p = _safe_path(path, root)
    if not p.is_file():
        raise FileNotFoundError(str(p))
    data = p.read_bytes()
    if len(data) > max_bytes:
        return (
            data[:max_bytes].decode("utf-8", errors="replace")
            + f"\n\n[... truncated at {max_bytes} bytes ...]"
        )
    return data.decode("utf-8", errors="replace")


def grep(
    pattern: str,
    path: str = ".",
    root: Path = REPO_ROOT,
    max_matches: int = MAX_GREP_MATCHES,
) -> list[str]:
    """Regex search. Returns up to `max_matches` lines as 'relpath:lineno: line'."""
    p = _safe_path(path, root)
    compiled = re.compile(pattern)
    matches: list[str] = []

    if p.is_file():
        targets: list[Path] = [p]
    else:
        targets = [
            f
            for f in p.rglob("*")
            if f.is_file() and ".git" not in f.parts and ".venv" not in f.parts
        ]

    resolved_root = root.resolve()
    for f in targets:
        try:
            lines = f.read_text().splitlines()
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(lines, start=1):
            if compiled.search(line):
                rel = f.relative_to(resolved_root)
                matches.append(f"{rel}:{lineno}: {line}")
                if len(matches) >= max_matches:
                    return matches
    return matches
