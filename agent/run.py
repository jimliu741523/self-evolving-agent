"""
agent.run — the user-facing dry-run harness (day 3).

Dry-run by default: queries the model for a proposal and prints it.
Does NOT modify any file, does NOT touch git. Human review stays in the loop.

Usage:
    python -m agent.run              # real model (needs ANTHROPIC_API_KEY)
    python -m agent.run --mock       # offline mock, no network
    python -m agent.run --save DIR   # also write proposal-<date>.md into DIR
"""
from __future__ import annotations

import argparse
import datetime
import os
from pathlib import Path

from agent.driver import (
    Proposal,
    propose_next_change,
    _anthropic_model,
    _mock_model,
)


def pretty_print(proposal: Proposal) -> None:
    bar = "-" * 60
    print(f"\n{bar}")
    print("  PROPOSED CHANGE")
    print(bar)
    print(f"  {proposal.change_description or '(empty)'}")
    print(f"{bar}\n")
    print("  WHY (paste into WHY.md)")
    print(bar)
    for line in (proposal.why_entry or "(empty)").splitlines():
        print(f"  {line}")
    print(f"{bar}\n")
    print("  -> dry run: nothing was committed.")
    print("     review above; if good, the human operator copies the WHY")
    print("     content into WHY.md and makes the proposed change.\n")


def save_proposal(proposal: Proposal, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    out = out_dir / f"proposal-{today}.md"
    out.write_text(
        f"# Proposal - {today}\n\n"
        f"**Change:** {proposal.change_description}\n\n"
        f"## WHY\n\n{proposal.why_entry}\n"
    )
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="agent.run",
        description="self-evolving-agent dry-run harness",
    )
    p.add_argument("--mock", action="store_true", help="use the offline mock model (no network)")
    p.add_argument("--save", type=Path, default=None, help="also write proposal-<date>.md into this directory")
    args = p.parse_args(argv)

    use_mock = args.mock or os.environ.get("SELF_EVOLVING_MOCK") == "1"
    model = _mock_model if use_mock else _anthropic_model

    proposal = propose_next_change(model)
    pretty_print(proposal)

    if args.save:
        out = save_proposal(proposal, args.save)
        print(f"  proposal saved to {out}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
