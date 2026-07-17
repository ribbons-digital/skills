# swarm

A coordinator skill for running multiple coding slices in parallel: decompose approved scope into slices, dispatch one swarm-worker per slice into its own git worktree, adjudicate escalations, review committed diffs against acceptance criteria, and integrate everything into one final PR.

The coordinator never implements a slice itself, enforces stop conditions (concurrency cap, worker staleness with respawn, fix-up and spec-debate caps, all-blocked halt), and is the only reviewer workers report to.

## Install

Copy this folder and its companion into your skills directory:

```bash
cp -R swarm swarm-worker ~/.claude/skills/
```

Restart the session so the skills are picked up.

## Requirements

- A harness with worker dispatch and two-way worker messaging (for example Claude Code subagents with a message channel); without a messaging channel, workers cannot block on escalations and the coordinator loses adjudication.
- Git worktree support in the repository.
- The companion `swarm-worker` skill installed where workers can read it; assignments reference it by path.

## When to invoke it

- "Orchestrate this approved scope across parallel workers"
- "Split this into slices and dispatch workers into worktrees"
- "Coordinate the swarm on this migration"

Never use it inside a worker thread; for a single solo slice with full PR workflow, use blaze.

## Family

`blaze` (solo, full workflow) / `swarm` (coordinator) / `swarm-worker` (dispatched worker).

## Scope evals

`evals/evals.json` holds labelled queries for validating the invocation description; re-run a skill-creator optimization loop after editing the description.
