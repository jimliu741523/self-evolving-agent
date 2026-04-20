"""
agent.driver — day-1 implementation.

Given the repo's current state (WHY.md, ROADMAP.md, file tree), asks a
model to propose the SMALLEST useful next change. Returns a structured
`Proposal` with a one-sentence change description and a paragraph-length
WHY.md entry.

The driver is intentionally small and readable. It's the thing the agent
will eventually modify as it evolves; keep it clean.

Usage:

    # real call — needs ANTHROPIC_API_KEY and `pip install anthropic`:
    python -m agent.driver

    # dry run with mock model, no network:
    SELF_EVOLVING_MOCK=1 python -m agent.driver
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Proposal:
    change_description: str
    why_entry: str


ModelFn = Callable[[str], str]
"""A callable that takes a prompt string and returns the model's response."""


SYSTEM_PROMPT = """\
You are an agent that improves its own codebase one commit at a time.
Read the current state (WHY.md, ROADMAP.md, file tree) and propose the
SMALLEST useful next change. One sentence describing the change, then
one paragraph for WHY.md explaining what you tried / learned / want next.

Format your response exactly as:

PROPOSAL: <one sentence>
WHY:
<paragraph>
"""


def read_state(root: Path = REPO_ROOT) -> str:
    """Collect the repo files the agent should consider before proposing."""
    parts: list[str] = []
    for name in ("WHY.md", "ROADMAP.md", "README.md"):
        p = root / name
        if p.exists():
            parts.append(f"=== {name} ===\n{p.read_text()}\n")
    tree_paths = sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.parts and ".venv" not in p.parts
    )
    parts.append("=== FILE TREE ===\n" + "\n".join(tree_paths) + "\n")
    return "\n".join(parts)


def parse(response: str) -> Proposal:
    """Parse a model response of the expected format into a Proposal."""
    proposal_text = ""
    why_lines: list[str] = []
    mode: str | None = None
    for line in response.splitlines():
        if line.startswith("PROPOSAL:"):
            proposal_text = line[len("PROPOSAL:") :].strip()
            mode = "proposal"
        elif line.startswith("WHY:"):
            mode = "why"
            rest = line[len("WHY:") :].strip()
            if rest:
                why_lines.append(rest)
        elif mode == "why":
            why_lines.append(line)
    return Proposal(
        change_description=proposal_text,
        why_entry="\n".join(why_lines).strip(),
    )


def propose_next_change(model: ModelFn, root: Path = REPO_ROOT) -> Proposal:
    state = read_state(root)
    prompt = f"{SYSTEM_PROMPT}\n\nCurrent repo state:\n\n{state}"
    return parse(model(prompt))


def _anthropic_model(prompt: str) -> str:
    """Real call. Requires the `anthropic` package and ANTHROPIC_API_KEY."""
    try:
        from anthropic import Anthropic
    except ImportError as e:
        raise RuntimeError("install the anthropic package: pip install anthropic") from e
    client = Anthropic()
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


def _mock_model(prompt: str) -> str:
    """Placeholder for tests and local demos. Doesn't touch the network."""
    del prompt
    return (
        "PROPOSAL: sketch a POLICY.md describing when the driver may auto-commit vs. require human review.\n"
        "WHY:\n"
        "ROADMAP slated POLICY.md for day 4, but deciding the review policy now gives every later commit "
        "a concrete rule to reference. A first draft with three tiers (human-reviewed, soft-auto with "
        "post-hoc audit, full-auto for trivial changes) is enough to iterate on — the important thing is "
        "getting a specific rule into the repo so we stop implicitly deciding case by case."
    )


def main() -> None:
    model: ModelFn = (
        _mock_model if os.environ.get("SELF_EVOLVING_MOCK") == "1" else _anthropic_model
    )
    proposal = propose_next_change(model)
    print(f"PROPOSAL: {proposal.change_description}\n")
    print("WHY:")
    print(proposal.why_entry)


if __name__ == "__main__":
    main()
