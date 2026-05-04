"""
agent.tools — inspector + write tools.

Day-2 read-only tools:
- `ls(directory)` — list visible entries of a directory inside the repo
- `cat(path)` — read a file (truncated at a byte limit for safety)
- `grep(pattern, path)` — regex search through a file or a subtree

Day-5 write tool (this commit):
- `write_file(relative, content, allow_t1)` — write content to a path
  inside the repo. Refuses paths in the T1-locked allowlist (`agent/`,
  `POLICY.md`, `tests/`, `Makefile`) unless `allow_t1=True` is passed
  explicitly — and even then is just a Python function call, not an
  endorsed action by the agent. The driver does NOT have any code path
  that calls `write_file` autonomously; that change requires a separate
  reviewed commit per POLICY.md.

All paths refuse to resolve outside the repo root.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Safety caps — kept conservative on purpose.
MAX_CAT_BYTES = 100_000
MAX_GREP_MATCHES = 50
MAX_WRITE_BYTES = 200_000

# Paths the agent must never edit autonomously (per POLICY.md T1).
# Match by path-prefix relative to repo root.
T1_LOCKED_PREFIXES = (
    "agent/",
    "tests/",
    "POLICY.md",
    "Makefile",
)


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


def _is_t1_locked(relative: str) -> bool:
    rel = relative.lstrip("./")
    for prefix in T1_LOCKED_PREFIXES:
        if rel == prefix or rel.startswith(prefix.rstrip("/") + "/") or rel.startswith(prefix):
            return True
    return False


def write_file(
    relative: str,
    content: str,
    allow_t1: bool = False,
    root: Path = REPO_ROOT,
) -> Path:
    """
    Write `content` to a repo-relative path. Creates parent directories
    as needed. Refuses to escape the repo root. Refuses paths in the
    T1-locked allowlist unless `allow_t1=True`.

    `allow_t1` is intentionally not the default: even with True it is a
    plain Python flag, not an authorization. POLICY.md restricts T1
    edits to humans; this function exists for the human reviewer's
    convenience (e.g. applying an agent's reviewed proposal), not as a
    knob the driver may flip.

    Caps content at MAX_WRITE_BYTES to prevent runaway writes.
    """
    if len(content.encode("utf-8")) > MAX_WRITE_BYTES:
        raise ValueError(
            f"write_file content exceeds {MAX_WRITE_BYTES} byte cap"
        )
    if _is_t1_locked(relative) and not allow_t1:
        raise PermissionError(
            f"path {relative!r} is T1-locked per POLICY.md; pass allow_t1=True to override"
        )
    path = _safe_path(relative, root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path
