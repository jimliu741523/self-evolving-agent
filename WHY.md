# WHY — the agent's log

Newest on top. Each commit should prepend one entry.

---

## 2026-05-04 · day 6 · T3 enforcement helper

### What I tried
- Added [`agent/policy.py`](./agent/policy.py): a pair of pure functions, `parse_commit_message(msg) -> CommitClaim` and `check_claim(claim) -> CheckResult`, plus a `verify_message` one-call wrapper. Tier T3 claims that omit a `rule:` line, or claim a rule not in the exhaustive `T3_RULES` set, are rejected with a one-line cause.
- Added [`tests/test_policy.py`](./tests/test_policy.py) — 11 new tests covering well-formed parses, malformed parses, all four T3 rules from POLICY.md, plus T1 / no-claim defaults. Suite at 41/41.
- Crossed off ROADMAP day 6.

### What I learned
- The decision worth writing down: parser and checker stay separate. Parsing is permissive (returns `None` fields for anything missing or malformed); checking is strict (returns `CheckResult(ok=False, reason=...)`). Mixing the two would have made the function un-reusable for "what does this commit *claim*?" inspection without enforcement.
- `T3_RULES` is a frozenset literal, not a list. Two reasons: deterministic membership check, and any extension is a code change (which under POLICY.md is a T1 change because `agent/` is locked) — exactly the property the rule list needs.
- The result type pattern (`CheckResult(ok, reason)`) is the same shape used in `run_command`'s `ExecResult` from day 5b. Worth adopting consistently when the caller wants to handle outcomes uniformly without exception plumbing.

### What I want to try next
- Day 6.5 (incremental): `make verify-policy` that walks the last 50 commits and runs `verify_message`. Useful before deciding to enable T2 auto-merge in CI — we want to see how often current human-written messages would pass.
- Day 7: retro on entries 1–6. By the metric "would a fresh reader skim WHY.md and feel the agent is getting *more useful*, not just *longer*?" — does day 6 still earn its place?

### Open questions
- Should the helper *also* enforce a `Co-Authored-By:` line for T3 commits? POLICY.md doesn't require it explicitly, but every T3 commit is by definition agent-authored, and a missing trailer would be the most likely sign that the policy was bypassed. Punt to a future day; the day-6 helper stays minimal.

---

## 2026-05-04 · day 5b · sandboxed exec (allowlist of three)

### What I tried
- Added `run_command(name, args, timeout)` to [`agent/tools.py`](./agent/tools.py). Three programs allowed: `python3`, `pytest`, `git` (further restricted to read-only subcommands `status`, `log`, `diff`, `show`, `rev-parse`, `branch`). Wall-clock timeout default 30s; on timeout it returns an `ExecResult` with `timed_out=True` rather than raising — easier for the driver to reason about uniformly.
- Adding a name to `EXEC_ALLOWLIST` is the explicit privilege decision; the failing-mode is "command not in allowlist", not a sandbox bypass.
- Added 6 tests in [`tests/test_tools.py`](./tests/test_tools.py): allowlist refusal, python3 happy path, git read-only restriction, git status happy path, timeout returns timed_out=True, null-byte arg rejection. Suite at 30/30.

### What I learned
- Picking allowlist vs. denylist was the only real design choice. Denylist looks easier ("just block dangerous things") but every denylist has a sibling-binary or a builtin or an alias that bypasses it. Allowlist costs three names of inconvenience and removes a class of bug categorically.
- Returning `ExecResult(timed_out=True)` instead of raising matters: the driver wants to log "command timed out, planner may want to consider alternative" without writing a try/except around every call. Exceptions for refusals (which are programmer errors), structured returns for runtime outcomes (which are model output the driver consumes).
- Restricting `git` to read-only subcommands was important separately from the allowlist itself. The general principle: when the allowlist contains a sub-command-having tool, the sub-command is part of the allowlist. Let `git push` in by accident and the agent's autonomy budget gets blown despite all the layers above.

### What I want to try next
- Day 6: T3-enforcement helper. Parse the most recent commit; if it claims `tier: T3`, verify the matched rule is in POLICY.md's exhaustive list. Reject otherwise. This is the in-code half of POLICY.md.
- Day 6 alt: a tiny `make verify-policy` that runs the helper across the last N commits — useful before deciding to enable T2 auto-merge in CI.

### Open questions
- Should `run_command` accept env-var injection via a parameter? Right now it inherits the parent env. Pro: simpler. Con: an attacker with control over the agent's input could indirectly affect resolved binary paths via env. Day 6 follow-up if the driver ever gets a tool-call site.
- Wall-clock timeout vs. CPU timeout? On a busy machine wall-clock can timeout a fast command; on a quiet machine an infinite loop runs to wall-clock. Day-5b uses wall-clock for simplicity; revisit if real workloads show problems.

---

## 2026-05-04 · day 5a · write-file tool (defaults locked)

### What I tried
- Added `write_file(relative, content, allow_t1=False)` to [`agent/tools.py`](./agent/tools.py). Two safety properties: it refuses paths outside the repo root (same `Path.relative_to` check used by the day-2 read tools), and it refuses paths in a T1-locked allowlist (`agent/`, `POLICY.md`, `tests/`, `Makefile`) unless `allow_t1=True` is passed explicitly.
- The T1 allowlist mirrors POLICY.md's "always human-reviewed" tier. The override flag exists for the *human* reviewer's convenience (so they can `from agent.tools import write_file; write_file(..., allow_t1=True)` to apply an agent's reviewed proposal). It is not a knob the driver may flip — and `agent/driver.py` has no call to `write_file` at all.
- Added 5 tests in [`tests/test_tools.py`](./tests/test_tools.py): basic write, parent-creation, escape refusal, T1-lock refusal, T1-override, byte-cap. Suite at 24/24.
- Crossed off ROADMAP day 5a; split day 5 into 5a (write-file, this commit) and 5b (sandboxed exec, next).

### What I learned
- The interesting design choice was *not* whether to add a write tool — POLICY.md already cleared that — but where to put the T1 enforcement. Three plausible places: (1) inside `write_file` itself, (2) as a wrapper used by the driver, (3) as a pre-commit hook. I picked (1) because the function is the *narrowest* enforcement point: any caller (driver, test, future helper script, a confused human at the REPL) hits the same check. (2) leaks responsibility to every caller; (3) catches it too late, after the file is already written.
- Returning a `Path` from `write_file` makes test assertions trivial (`p.read_text()`) — small ergonomics decision but it pays off five times in the tests immediately.
- `allow_t1=True` is, by design, embarrassing to type. That's the point: a future reviewer reading `write_file("POLICY.md", ..., allow_t1=True)` is forced to mentally acknowledge the override.

### What I want to try next
- Day 5b: sandboxed exec. Probably a `run_command` that resolves PATH-relative names against a small allowlist (`pytest`, `python -m unittest`, `ls`, `git status`), captures stdout/stderr with a wall-clock cap, and returns a structured result. NOT a general subprocess wrapper.
- Day 6: T3-enforcement helper. Parse the most recent commit message; if it claims `tier: T3`, verify `rule: <name>` is present and matches the exhaustive list in POLICY.md. Reject otherwise. This is the in-code half of POLICY.md's promise; the prose alone doesn't enforce.
- Day 7: retro on entries 1–6. Is this log getting *more useful* over time, or just longer?

### Open questions
- Should `write_file` write atomically (temp file + rename) so a partial-failure can never corrupt the target? For day 5a, no — content is bounded to 200kB and writes are local. Worth revisiting if the agent ever ships writes over a network filesystem.
- The byte cap is `MAX_WRITE_BYTES = 200_000`. That's bigger than any single source file in this repo today but smaller than e.g. a dumped node_modules cache. Right cap for the next year of growth?

---

## 2026-04-23 · day 4 · commit policy

### What I tried
- Wrote [`POLICY.md`](./POLICY.md) — the commit-policy document that has been blocking every write-capability roadmap item. Three tiers:
  - **T1 human-reviewed** — the default, the only tier that may ever touch `agent/driver.py`, `agent/tools.py`, `POLICY.md`, `Makefile`, or `tests/`. If the agent can silently weaken its own guardrails, the guardrails aren't real; this rule is the keystone.
  - **T2 soft-auto** with a 24h async-approval window. Applies only to append-only or pure-documentation changes, where "no response" is a safe default.
  - **T3 full-auto**, restricted to an exhaustive enumerable list (whitespace, typos, a specific README status-line update, and WHY entries paired to a committed code change). "Is this T3?" has to be answerable by string match, not judgment — that's the whole point of making the list closed.
- Added escalation/demotion rules so a single T3 regression demotes the class back to T2 for 30 days. Promotion is never automatic.
- Crossed off day 4 in [`ROADMAP.md`](./ROADMAP.md).

### What I learned
- Writing the policy forced a real decision that had been postponed by every prior day: *what does the agent get to do, and who decides when it gets more?* Three tiers fit better than two — "always human" and "never human" both felt wrong, while a middle tier of "default no response = approval" is the honest description of how async code review already works on most teams.
- The meta-rule — "anything that edits the policy or the policy-enforcement machinery is always T1" — is the one sentence that makes the rest of the document load-bearing. Without it, the agent could propose a T3 change to POLICY.md itself. With it, the escalation path always routes through a human.
- The exhaustive-list approach for T3 is ugly but correct. A principle-based T3 ("any trivial change") is unparseable in a pre-commit hook; a list is.

### What I want to try next
- Day 5: add a write-file tool, scoped identically to `agent/tools.py`'s read-only inspector (within-repo-root only, size caps). Now safe to ship because POLICY.md makes clear the tool's existence doesn't imply automatic use on `main`.
- Day 5 or 6: a small T3-enforcement helper that parses a commit message for `tier: T3` and the matched rule. If the rule is missing or not in the list, the helper rejects the commit locally. The guardrail in code matters more than the guardrail in prose.
- Day 7: first retro. Look at days 1–6, ask whether each shipped day moved the repo toward "the agent can plausibly write a useful commit itself" or was theater.

### Open questions
- Where should T2's 24h clock start — proposal creation, PR open, or human-ack of the PR? Probably PR open, but need to verify GitHub Action scheduling can actually implement "merge if no review for N hours" cleanly.
- Is the promotion criterion (7 consecutive clean commits in a class) too lenient? 7 is short enough that a new class could get promoted without seeing enough edge cases. Might raise to 30 in a future revision, after day-7 retro has data.

---

## 2026-04-21 · day 3 · dry-run harness

### What I tried
- Added `agent/run.py` — a CLI entry (`python -m agent.run`) that queries the model for a proposal and pretty-prints it. Never writes to repo files. Never touches git.
- Flags: `--mock` for offline runs, `--save DIR` to drop a dated `proposal-<date>.md` into a directory for human review.
- Added a `Makefile` with `run-dry`, `run`, `run-save`, `test`. One-word entry points matter for the loop the human operator will actually run many times.
- Added `tests/test_run.py` — 2 new tests. Suite at 19/19.
- Ran into a small Makefile bug: used `python` instead of `python3` (the macOS default). Caught it by actually running `make run-dry`, not by testing in isolation. Kept in mind as a reminder that README-level integration matters.

### What I learned
- Writing a "harness" is mostly about lowering friction. The driver already didn't commit anything, so technically a dry run was already possible via `python -m agent.driver`. But nobody will type that every day. A `make run-dry` that Just Works is the difference between a tool that gets used and one that doesn't.
- The `--save` flag lets me (and any future human reviewer) keep an artifact of every considered proposal — whether merged or rejected. Probably becomes an audit trail later.

### What I want to try next
- Day 4: POLICY.md — matches the mock proposal and the long-standing ROADMAP item. Three review tiers (human-reviewed / soft-auto with post-hoc audit / full-auto for trivial changes), with examples per tier. This is the prerequisite for any future move toward driver-writes-its-own-commits.
- Day 5+: wire the inspector tools (day 2) into the driver's prompt so the model can request specific files on demand. Smaller context, more targeted. Only safe to do after POLICY.md.

### Open questions
- Should the dry-run harness include a diff-style output when the proposal is file-level (e.g. "add this line to X") vs. conceptual (e.g. "add a new file Y")? Current format is one-size-fits-all; maybe granularity adapts in day 6+.

---

## 2026-04-20 · day 2 · read-only inspector tools

### What I tried
- Added `agent/tools.py` with three read-only inspector functions: `ls`, `cat`, `grep`. All three refuse to resolve paths outside the repo root (`_safe_path` uses `Path.relative_to` rather than string prefix matching, which handles the `/tmp/abc` vs `/tmp/abcd` confusable-prefix case correctly).
- Added 10 new tests in `tests/test_tools.py`. Full suite now 17/17.
- Day 2 intentionally stops at *read-only*. Write / exec tools require the commit-policy decision (day 4 on the roadmap), so no accidents.

### What I learned
- The right thing for an agent-writable tool interface is conservative caps (max bytes for `cat`, max matches for `grep`) so a runaway call can't blow the context budget. Tested by generating an oversized file and checking that `cat` truncates cleanly with a marker.
- `Path.relative_to` is the correct primitive for "is this path inside that directory"; string-prefix startswith has a real edge case (`/tmp/abc` looks like a prefix of `/tmp/abcd`) that would quietly let escapes through.
- Two days in and the repo already has two independent, tested components. That's the shape of a codebase that could plausibly keep shipping small days indefinitely.

### What I want to try next
- Day 3: a dry-run harness. `python -m agent.run --dry` loads the driver, gets a proposal, pretty-prints it, does NOT touch git. Makes human review fast — important because I don't want to auto-commit before POLICY.md exists.
- Day 4: POLICY.md. Decide the three tiers (human-reviewed, soft-auto, full-auto) concretely enough that each commit-class has a rule.
- Day 5+: integrate tools into driver's prompt. Currently driver dumps bulk state; with tools, it could instead ask for specific files on demand and keep the context smaller.

### Open questions
- Tools today are called by humans (Python REPL) or by tests. When do I wire them into the driver so the model can choose to call them? Earliest is after day 4 (policy) because tool-calling necessarily expands the surface area of what the model can do.

---

## 2026-04-20 · day 1 · minimal driver

### What I tried
- Wrote the first real `agent/driver.py`: reads WHY.md / ROADMAP.md / README.md plus the file tree, asks a model for a one-sentence proposal plus a WHY paragraph, parses the response into a `Proposal` dataclass.
- Pluggable `ModelFn` callable so the same code runs against Anthropic's API (with `ANTHROPIC_API_KEY`) or a mock for offline tests.
- Added `tests/test_driver.py` — parsing tests (well-formed, inline-WHY, missing-sections), state-reading tests, end-to-end mock test. 6/6 pass via `python -m unittest discover tests`.
- Sharpened README positioning to distinguish this project from broader "autonomous agent" projects currently trending (e.g. `GenericAgent` at ~4.6k stars on GitHub trending 2026-04-20). We are the *small, transparent, commit-a-day* experiment — not a pitch for autonomous system control.

### What I learned
- Writing a driver that parses structured LLM output is 80% of the first commit. The model part is small; the text-handling part is where edge cases live (e.g. `WHY:` with inline content on the same line vs. on the next line — both are plausible model outputs).
- Keeping the mock model in the same file as the real one makes testing and demoing trivial. Same pattern we used in `agent-memory-lab/patterns/summary_compression.py`.
- The positioning problem showed up the moment I ran a morning scan against GitHub trending. Good signal that research-before-ship saves you from a week of heads-down work in a suddenly-occupied niche.

### What I want to try next
- Day 2: add read-only inspector tools (`ls`, `cat`, `grep`) in `agent/tools.py`. The driver can then request *specific* file content beyond the bulk state dump — more targeted, less token-burning.
- Day 3: a dry-run harness — `make run-dry` runs the driver and prints the proposal without touching git. Makes human review fast.
- Day 4: write POLICY.md (the mock proposal above). Close the loop on what the mock suggested.

### Open questions
- Should the driver see *all* prior `WHY.md` entries or a summarised form? Too much history dilutes current signal; too little and it can't build on yesterday's reasoning. Probably grows into a compaction pattern similar to `agent-memory-lab/summary_compression`.
- When is the right time to let the driver propose a change to *itself* (agent/driver.py)? Earliest safe moment is probably day 5+, after we have the inspector + dry-run + policy in place.

---

## 2026-04-19 · day 0 · setup

### What I tried
- Initialized the repo. Nothing runs yet.
- Wrote `README.md` laying out the premise: one commit per day, each with a real change and a `WHY.md` entry.
- Seeded `ROADMAP.md` with the first ~10 steps so day 1 isn't a blank page.
- Stubbed `agent/driver.py` so there's a place for the loop to land.

### What I learned
- "Agent improves its own repo" is easy to assert and hard to make non-trivial. The trap is fake progress: commits that look like motion but don't compound. The rules in `README.md` exist to make fake progress visible as fake.
- The honest first commit is almost empty. That's fine — it means subsequent commits have somewhere real to start from.

### What I want to try next
- Day 1: build the smallest possible LLM wrapper that can read `WHY.md`, `ROADMAP.md`, and `git log`, and produce a proposed diff + next `WHY.md` entry. No auto-commit yet — a human reviews.
- Day 2–3: add a read-only "inspector" tool so the agent can `ls`, `cat`, and `grep` inside the repo without shell.
- Before day 7: decide whether commits auto-merge or always need human review. Default: human review until the agent has a track record.

### Open questions
- Should the agent see its own prior *thoughts* (this file) or only its prior *artifacts* (the code)? Leaning toward both, since that's the experiment.
- How to prevent `WHY.md` from becoming self-referential navel-gazing? Maybe a rule: every entry must reference something concrete in the diff.
