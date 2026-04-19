# WHY — the agent's log

Newest on top. Each commit should prepend one entry.

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
