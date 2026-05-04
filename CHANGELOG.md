# CHANGELOG

Newest on top. Tracks meaningful day-by-day capability growth. Cosmetic edits and small README touch-ups are not logged here — they live in the WHY.md entry that pairs with each commit.

## 2026-05-04 — day 5a
- **Write-file tool** added (`agent/tools.py::write_file`). Refuses paths in T1-locked allowlist (`agent/`, `POLICY.md`, `tests/`, `Makefile`) by default; `allow_t1=True` for human reviewers applying agent-proposed changes. Driver still has no autonomous call site. Suite 24/24.

## 2026-04-23 — day 4
- **POLICY.md** shipped — three commit-tier scheme. T1 human-reviewed (default; permanent lock on `agent/`, `POLICY.md`, `tests/`, `Makefile`); T2 soft-auto with 24h async-approval window; T3 full-auto with exhaustive enumerable rule list. Escalation/demotion rules: one T3 regression demotes the class back to T2 for 30 days. Prerequisite for every write-capability roadmap item that follows.

## 2026-04-21 — day 3
- **Dry-run harness** in [`agent/run.py`](./agent/run.py) + [`Makefile`](./Makefile). Pretty-prints a proposal; optional `--save DIR` writes a dated `proposal-<date>.md` for human review. Never commits.
- 2 new tests; suite 19/19.

## 2026-04-20 — day 2
- **Read-only inspector tools** in [`agent/tools.py`](./agent/tools.py): `ls`, `cat`, `grep`. Each scoped via `Path.relative_to`; refuses directory escape. Conservative caps on `cat` bytes and `grep` matches.
- 10 new tests; suite 17/17.

## 2026-04-20 — day 1
- **Driver** in [`agent/driver.py`](./agent/driver.py) — pluggable `ModelFn` runs against Anthropic API or an offline mock. Reads WHY/ROADMAP/README + file tree and parses a structured proposal.
- 6 tests at this point.

## 2026-04-19 — day 0
- Initial commit: README, ROADMAP, WHY day-0 entry, LICENSE, driver stub.
