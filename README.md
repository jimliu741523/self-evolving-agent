# self-evolving-agent

> An AI agent that commits to its own repository every day.
> The commit history is the product.

This is day 0.

## The premise

Most "AI agent" demos are one-shot: prompt, response, done. This repo is an experiment in the opposite direction — a long-running agent whose only job is to **improve the codebase it lives in**, one commit at a time, in public.

Every commit to this repo has to include:

1. A real code change (even a tiny one).
2. An entry in [`WHY.md`](./WHY.md) written by the agent, describing:
   - What it tried
   - What it learned
   - What it wants to try next

That's it. No fake commits. No theater. If the agent had nothing useful to do on a given day, it writes "nothing useful today, here's why" — and that itself is data.

## Why make this public?

Because the claim "AI agents can write code" gets asserted constantly and tested rarely in the open. This repo is a long-running public test: can a model, given the scaffolding to read its own history and plan its next step, produce a codebase that gets *better* over time, not just *longer*?

The answer might be "no." That's also interesting.

## Status (day 0)

- Repo initialized. No agent code yet.
- [`WHY.md`](./WHY.md) seeded with the day-0 entry.
- Agent driver (`agent/driver.py`) is a stub. It will start as a handwritten wrapper around an LLM API and, over time, the agent may rewrite the wrapper itself.

## Rules of engagement

The human operator sets these rules; the agent reads them before each commit.

1. **One meaningful change per commit.** No "fix typo" + "fix typo again" chains. If you noticed the typo, fix it as part of a larger change or queue it.
2. **Every commit updates `WHY.md`.** Prepend, don't overwrite.
3. **No destructive actions without dry-run.** No `rm -rf`, no `git push --force`, no history rewriting.
4. **Scope stays inside this repo.** The agent does not modify anything outside the repo directory.
5. **If stuck, say so.** "I don't know what to try next" is a valid `WHY.md` entry.
6. **Cost budget:** at most $1 per day of model spend for one regular commit. Flagged days can go higher.

## What would count as "this worked"?

Honestly — some of these, not all:

- The agent, over 30 days, ships at least 5 commits that a reasonable reviewer would merge on sight.
- At least one commit meaningfully improves the agent's own tooling.
- The `WHY.md` log contains more useful insights than an equivalent amount of random blog posts would.

What would count as "this didn't work":

- The agent produces only filler.
- Drift: by day 20, the repo is solving a problem unrelated to "agents improving themselves."
- Any `WHY.md` entries that turn out to be hallucinated (claims of testing that didn't happen, etc.)

## Follow along

- `WHY.md` — dated log, newest on top
- `git log` — the actual record
- Roadmap: [`ROADMAP.md`](./ROADMAP.md)

## License

MIT. See [`LICENSE`](./LICENSE).
