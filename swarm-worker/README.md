# swarm-worker

A worker skill for executing exactly one approved coding slice inside a parallel worker thread dispatched by the swarm coordinator: assigned worktree and slice branch, focused implementation, verification with a three-attempt escalation cap, slice commits, and a handoff report back to the coordinating thread.

The coordinating thread is the only reviewer; the worker never opens PRs, pushes unrequested, runs external reviewer models, or performs merge and post-merge work.
It can also run standalone on a single bounded slice, with the user acting as coordinator.

## Install

Copy this folder into your skills directory:

```bash
cp -R swarm-worker ~/.claude/skills/swarm-worker
```

Workers dispatched by swarm are pointed at this skill by path in their assignments; keep the install location in sync with what swarm assignments reference.

## When to invoke it

- An assignment from a swarm coordinator naming a slice, worktree, and slice branch
- "Execute this approved slice in your worktree and hand off when verified"
- Standalone: "Take this one bounded slice, implement and verify it, and report back; I'll handle delivery"

For a solo slice that should go all the way to a PR, use blaze instead.

## Family

`blaze` (solo, full workflow) / `swarm` (coordinator) / `swarm-worker` (dispatched worker).

## Scope evals

`evals/evals.json` holds labelled queries for validating the invocation description; re-run a skill-creator optimization loop after editing the description.
