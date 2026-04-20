# Roadmap

A rough ordering. The agent may reorder or delete items as it goes — but it must say why in `WHY.md`.

## Near-term (days 1–10)

- [x] Day 1 · Smallest possible LLM wrapper in `agent/driver.py` — reads files, proposes diffs, writes `WHY.md` entry. No auto-commit. ✅ 2026-04-20
- [ ] Day 2 · Read-only inspector tools (`ls`, `cat`, `grep`) in `agent/tools.py`.
- [ ] Day 3 · Test harness: `make run-dry` runs the agent against the current repo state and dumps proposed diff to stdout.
- [ ] Day 4 · Decide commit policy: always-human-review vs conditional-auto-merge. Write it into `POLICY.md`.
- [ ] Day 5 · Add a write-file tool + sandboxed exec.
- [ ] Day 7 · Retro: are the `WHY.md` entries getting more or less insightful? (objective-ish: word-level entropy, subjective: would an engineer find day-7 entry more useful than day-1?)
- [ ] Day 10 · First fully-agent-authored commit (i.e. the driver writes the change itself instead of the human typing). Reviewer still human.

## Mid-term (days 11–30)

- [ ] Add a "try-it-yourself" section to README so visitors can clone and run the agent locally.
- [ ] Add a benchmark: does each week's agent ship more useful code than the previous week's, on a fixed hold-out task?
- [ ] The agent starts improving its own tools (inspector → richer queries; driver → better planning prompts).
- [ ] A CHANGELOG.md generated from `WHY.md` entries.

## Long-term (days 31+)

- [ ] Consider letting the agent reach beyond this repo (e.g. read another repo it depends on). Only after strong safety gates.
- [ ] Month-in-review blog-style post in the repo itself, written by the agent, summarizing learnings.
- [ ] Invite human contributors: issues that the agent triages first, then humans decide.

## Rules for editing this file

- Only the agent edits it, as part of a commit that also updates `WHY.md`.
- Items can be moved, crossed off, or deleted — but the `WHY.md` entry has to explain.
- New items go at the bottom unless there's a reason to slot in earlier.
