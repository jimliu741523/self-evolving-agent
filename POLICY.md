# POLICY

How commits from the agent reach `main`. Three tiers, from strict to permissive. This file is load-bearing — every future capability expansion in `ROADMAP.md` has to declare which tier it falls under before it ships.

> The default tier for any new change class is **T1 (human-reviewed)**. A change can be promoted to T2 or T3 only after 7 consecutive commits of that class have landed cleanly under the higher tier.

---

## T1 — Human-reviewed (default)

**Rule.** The agent proposes. A human reads the proposal and either applies it or rejects it. The agent does not touch git state.

**Applies to.** Everything not explicitly listed below. First and foremost, anything that edits `agent/driver.py`, `agent/tools.py`, `POLICY.md`, `Makefile`, or `tests/` — the machinery that enforces the other tiers.

**Mechanics.**
- Agent produces a `proposal-<date>.md` via `make run-save` (see [`agent/run.py`](./agent/run.py)).
- Human reviews, applies by hand or with `git apply`, commits themselves with `Co-Authored-By:` attribution.
- On rejection, the reason goes into the next `WHY.md` entry so the agent learns from the outcome.

**Rationale.** The machinery of self-modification has to be reviewed by a human every time. If the agent can silently weaken its own guardrails, the guardrails aren't real.

---

## T2 — Soft-auto (PR + async approval)

**Rule.** The agent opens a pull request against `main`. A human has **24 hours** to react (comment, request changes, or close). If no reaction, the PR auto-merges.

**Applies to.**
- New `WHY.md` entries (append-only).
- Additions to `ROADMAP.md` (not edits to existing items).
- New test cases that only add coverage (no modification of existing tests).
- Documentation: README, per-module docstrings, comments.

**Mechanics.**
- Agent creates a branch, commits, pushes, opens PR with title `[T2] <one-line>`.
- Reviewer either approves, requests changes, or does nothing.
- After 24h with no response, CI-green PR merges. The merge commit links to the silent-approval log.
- The agent may NOT re-open a closed T2 PR without human acknowledgment.

**Rationale.** Append-only and documentation changes cannot degrade correctness. The 24h window keeps a human in the loop without requiring a synchronous response.

---

## T3 — Full-auto

**Rule.** The agent commits directly to `main` (or via fast-forward PR). No human step.

**Applies to.** Only the following, exhaustively:
- Whitespace-only formatting fixes.
- Typo corrections in text files (README, WHY, ROADMAP, POLICY itself).
- Updating `Currently: day N.` line in README.
- Appending a dated entry to `WHY.md` that corresponds to a committed code change (pairing only, not a freestanding write).

**Mechanics.**
- Each T3 commit must include in its commit body: `tier: T3` and the matched rule, e.g. `rule: typo fix`.
- Every 7 days a retrospective job audits T3 commits. Any commit that doesn't match an exhaustive rule is flagged for human review.

**Rationale.** Zero-risk cosmetic maintenance shouldn't need human attention. The exhaustive list exists so that "is this T3?" can be answered by string match, not judgment.

---

## Escalation and demotion

- Any T3 change that breaks a test: the agent demotes that change class back to T2 for 30 days.
- Any T2 PR that a human rejects with `reason: policy`: demote that change class to T1 for 30 days.
- Promotion is never automatic. A human explicitly moves an entry up a tier (and notes it in WHY.md).

---

## What this policy does NOT say

- **It doesn't grant the agent any write capability it doesn't already have.** At day 4, the agent is still dry-run only. T2 and T3 are specifications for *when* write access lands, not a switch.
- **It doesn't apply to dependencies or infrastructure.** Anything that touches `requirements.txt` / GitHub Actions / tokens / secrets is out of scope for all three tiers and requires human action every time.
- **It isn't a safety proof.** It's a process. The proof is the commit history holding up over weeks without incident.

---

## Revisions

| Date | Change | Tier affected |
|---|---|---|
| 2026-04-23 | Initial draft (day 4). | all three |
