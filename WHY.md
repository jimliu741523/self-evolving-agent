# WHY — the agent's log

Newest on top. Each commit should prepend one entry.

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
