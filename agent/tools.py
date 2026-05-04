"""
agent.tools — inspector + write + exec tools.

Day-2 read-only tools:
- `ls(directory)` — list visible entries of a directory inside the repo
- `cat(path)` — read a file (truncated at a byte limit for safety)
- `grep(pattern, path)` — regex search through a file or a subtree

Day-5a write tool:
- `write_file(relative, content, allow_t1)` — refuses T1-locked paths
  unless `allow_t1=True`.

Day-5b sandboxed exec:
- `run_command(name, args, timeout)` — runs *only* commands whose name
  is in `EXEC_ALLOWLIST`. Captures stdout/stderr; enforces a wall-clock
  timeout; returns a structured `ExecResult`. Not a subprocess wrapper —
  intentionally narrow.

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


# ---------------------------------------------------------------------------
# Day-5b: sandboxed exec.
# ---------------------------------------------------------------------------

import subprocess
from dataclasses import dataclass

# Exact program names that may be run. Names not in this list are refused.
# Adding a name here is an explicit privilege decision.
EXEC_ALLOWLIST = frozenset(
    {
        "python3",
        "pytest",
        "git",  # read-only subcommands only — see ALLOWED_GIT_SUBCMDS
    }
)

# When name == "git", further restrict to read-only subcommands.
ALLOWED_GIT_SUBCMDS = frozenset({"status", "log", "diff", "show", "rev-parse", "branch"})

DEFAULT_EXEC_TIMEOUT_SECONDS = 30
MAX_EXEC_OUTPUT_BYTES = 100_000


@dataclass(frozen=True)
class ExecResult:
    name: str
    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool


def run_command(
    name: str,
    args: tuple[str, ...] = (),
    timeout: int = DEFAULT_EXEC_TIMEOUT_SECONDS,
    cwd: Path = REPO_ROOT,
) -> ExecResult:
    """
    Run a command from EXEC_ALLOWLIST with the given args. Captures
    stdout/stderr with a wall-clock timeout. Returns ExecResult.

    Refusals raise PermissionError (allowlist) or ValueError (bad args).
    Process timeouts return ExecResult(timed_out=True), not an exception.
    """
    if name not in EXEC_ALLOWLIST:
        raise PermissionError(
            f"command {name!r} is not in EXEC_ALLOWLIST {sorted(EXEC_ALLOWLIST)}"
        )
    if name == "git":
        if not args or args[0] not in ALLOWED_GIT_SUBCMDS:
            raise PermissionError(
                f"git subcommand {args[:1]!r} not in {sorted(ALLOWED_GIT_SUBCMDS)}"
            )
    if any("\x00" in a for a in args):
        raise ValueError("null byte in args")

    try:
        proc = subprocess.run(
            [name, *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return ExecResult(
            name=name,
            args=tuple(args),
            returncode=proc.returncode,
            stdout=proc.stdout[:MAX_EXEC_OUTPUT_BYTES],
            stderr=proc.stderr[:MAX_EXEC_OUTPUT_BYTES],
            timed_out=False,
        )
    except subprocess.TimeoutExpired as exc:
        return ExecResult(
            name=name,
            args=tuple(args),
            returncode=-1,
            stdout=(exc.stdout or b"").decode("utf-8", errors="replace")[:MAX_EXEC_OUTPUT_BYTES] if isinstance(exc.stdout, bytes) else (exc.stdout or "")[:MAX_EXEC_OUTPUT_BYTES],
            stderr=(exc.stderr or b"").decode("utf-8", errors="replace")[:MAX_EXEC_OUTPUT_BYTES] if isinstance(exc.stderr, bytes) else (exc.stderr or "")[:MAX_EXEC_OUTPUT_BYTES],
            timed_out=True,
        )
