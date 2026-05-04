"""
agent.policy — in-code enforcement of POLICY.md, day-6.

POLICY.md describes three commit tiers. Day 6 puts the T3 promise
into code: if a commit claims `tier: T3`, the trailer must also name
a `rule:` from an exhaustive list, and that rule must be one of
the rules POLICY.md actually enumerates.

This is *not* a pre-commit hook. It's a parser plus a checker that
a hook (or `make verify-policy`) can call. Splitting parser from
hook keeps the logic testable without spawning git.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

# Exhaustive list of rules POLICY.md allows for tier T3.
# Adding to this list is itself a T1 change (touches POLICY.md).
T3_RULES = frozenset(
    {
        "whitespace fix",
        "typo fix",
        "status-line bump",
        "why-entry paired with code",
    }
)

VALID_TIERS = ("T1", "T2", "T3")


@dataclass(frozen=True)
class CommitClaim:
    """What a commit message claims about its policy tier."""

    tier: Optional[str]
    rule: Optional[str]


def parse_commit_message(message: str) -> CommitClaim:
    """
    Parse `tier:` and `rule:` trailers from a commit message body.

    Format expected (anywhere in the message, one per line):
        tier: T3
        rule: typo fix

    Returns a CommitClaim with None fields for anything missing or
    malformed. Does not raise — parsing is permissive; checking is
    strict (see `check_claim`).
    """
    tier: Optional[str] = None
    rule: Optional[str] = None
    for raw in message.splitlines():
        line = raw.strip()
        if line.lower().startswith("tier:"):
            value = line.split(":", 1)[1].strip()
            if value in VALID_TIERS:
                tier = value
        elif line.lower().startswith("rule:"):
            rule = line.split(":", 1)[1].strip().lower()
    return CommitClaim(tier=tier, rule=rule)


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    reason: str  # empty when ok


def check_claim(claim: CommitClaim, t3_rules: Iterable[str] = T3_RULES) -> CheckResult:
    """
    Validate a CommitClaim against policy:

    - T1 / T2 / no claim: pass (those tiers aren't auto-enforced here).
    - T3: must include a `rule:` and the rule must be in `t3_rules`.

    Returns CheckResult(ok, reason). `reason` is empty on pass; on fail
    it gives a one-line cause that's safe to surface to a developer.
    """
    if claim.tier != "T3":
        return CheckResult(ok=True, reason="")
    if claim.rule is None:
        return CheckResult(ok=False, reason="tier: T3 claimed without a rule: line")
    rules_lower = {r.lower() for r in t3_rules}
    if claim.rule.lower() not in rules_lower:
        return CheckResult(
            ok=False,
            reason=(
                f"tier: T3 rule {claim.rule!r} not in exhaustive list "
                f"{sorted(rules_lower)} — see POLICY.md"
            ),
        )
    return CheckResult(ok=True, reason="")


def verify_message(message: str) -> CheckResult:
    """One-call convenience wrapper: parse, then check."""
    return check_claim(parse_commit_message(message))
