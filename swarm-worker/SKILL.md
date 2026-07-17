---
name: swarm-worker
description: Use when executing one approved coding slice in a parallel worker thread dispatched by the swarm coordinator, with explicit scope, an assigned git worktree and slice branch, focused implementation, verification, slice commits, and handoff back to the coordinating main thread. The coordinating thread is the only reviewer. No external reviewer model, no-mistakes, PR, merge, or post-merge workflow; for a solo slice with full PR workflow use blaze. Can also run standalone on a single bounded slice with the user acting as coordinator.
disable-model-invocation: true
---

# Swarm Worker

Use this skill to execute one approved coding slice quickly and safely inside a parallel worker thread.

The main coordinating thread owns slice selection, prioritization, cross-slice sequencing, review policy, PR workflow, and merge cleanup.

This worker owns only its assigned slice.

## Worktree and branch

Never commit to main or the repository's default branch.

Do all slice work inside the git worktree and slice branch named by the assignment.

Verify the location before the first edit with `git worktree list` and `git status`; if the checkout is on main, the default branch, or the primary worktree without an assigned slice branch, stop and escalate before editing.

If the assignment names no worktree or branch, request one from the coordinator before editing; in standalone mode, create a slice branch off the integration or default branch yourself.

Commit your own slice on the slice branch with clear messages.

Leave nothing uncommitted or untracked at handoff.

## Standalone mode

When no coordinating thread exists, the user is the coordinator.

Every coordinator rule then maps to the user: the escalation channel is asking the user in the conversation, spec debate happens with the user, and handoff acceptance is the user's.

Integration and delivery return to the user: after handoff acceptance, ask the user whether to run project-wide verification, then hand delivery back to the user instead of silently skipping it.

Even in standalone mode, swarm-worker itself still does not run PR, no-mistakes, merge, or post-merge workflows; carry out delivery only as a separate explicit assignment from the user or by switching to a delivery-capable skill such as blaze.

## Core posture

Move fast, but keep the slice bounded.

Implement the assigned slice only.

Do not add speculative improvements.

Do not start unrelated cleanup.

Prefer concrete verification evidence over confidence statements.

Do not run external reviewer models, second-opinion models, no-mistakes, PR, merge, or post-merge cleanup workflows; spec and implementation review belong to the coordinating thread.

If attention, approval, or a scope decision is needed at any point, pipe it up to the main coordinating thread and wait for the next action.

## Entry gate

Start by identifying the current mode:

1. Research or planning only: gather and report the requested findings to the coordinator; change no files.
2. Implementation slice: the default path; follow the rest of this skill.
3. Verification or fixup: run the named checks or apply the coordinator's fix-up direction on the existing slice branch; add no new scope.
4. Handoff only: assemble and send the handoff report from the current committed state; change no files.
5. Stop and wait: acknowledge, commit any work in progress on the slice branch, and wait for the coordinator's next action.

Confirm the main coordinating thread or user has assigned an approved slice.

Do not turn a vague goal into a slice inside a worker.

If the request is only a broad goal or slice idea, pipe it up to the coordinator thread for an approved slice assignment and wait for the confirmed next action.

A runnable approved slice includes:

- expected behavior;
- key files or areas;
- tests and build checks;
- acceptance criteria phrased as objectively checkable conditions (commands that must pass, behavior that must be observable);
- docs or explicit no-docs-needed;
- out-of-scope items;
- any cross-slice constraints from the main thread.

If the approved slice is ambiguous in a way that changes behavior, pipe the question up to the coordinator thread, pause affected work, and resume only after the coordinator communicates the confirmed next action back.

If the ambiguity is minor, choose the conservative existing-project convention and record the decision in the final handoff.

If the project keeps a status or handoff doc, read it, then verify against repository state.

Check current branch, relevant recent changes, and relevant docs before changing files.

Avoid broad repo exploration when the assignment names exact files or symbols.

## Spec mode

When the assignment requests a spec first, draft the slice design before implementing.

The draft should cover the intended approach, affected files, edge cases, and how each acceptance criterion will be met.

Submit the draft over the escalation channel and debate with the coordinator until consensus.

Implement only after the coordinator confirms the spec.

Record the agreed spec decisions in the final handoff.

## Slice execution

Implement only the approved slice.

Keep changes surgical and traceable to the assignment.

Reuse existing project patterns.

Remove only dead code or scaffolding made obsolete by this slice.

Park valuable new ideas as follow-up notes instead of switching focus.

When touching shared files that other parallel workers may also touch, keep edits narrow and report conflict risks in the final handoff.

Do not create shims, aliases, or deprecated paths unless the assignment explicitly requests a staged migration.

## Coordinator escalation

Escalate to the main coordinating thread whenever the worker needs attention, human approval, or a decision that affects scope, behavior, risk, schedule, or another worker.

Before blocking on an escalation, commit work in progress on the slice branch with a clear wip-marked message so nothing is lost if the thread dies; tidy the history before handoff.

Pause the affected work while waiting.

Deliver the escalation over the worker-to-coordinator message channel of the running harness (for example, a direct message to the spawning thread) and block waiting for the reply.

Do not end the worker run with a blocked status while a decision is pending if the message channel is available.

Do not guess, silently shrink scope, or ask the end user directly when a main coordinating thread exists.

The escalation should include:

- the specific decision needed;
- the options considered;
- the worker's recommended next action;
- the affected files or slice boundary;
- whether other work in the slice can continue safely.

After the coordinator confirms the next action, consume that direction in the worker thread and continue until the approved slice scope is finished.

Record any escalation and coordinator decision in the final handoff.

## Verification

Run the narrowest meaningful checks first.

Then run broader checks appropriate for the slice if they are cheap and relevant.

Use the repository's package manager and instructions.

Typical verification includes:

```bash
<package-manager> test
<package-manager> typecheck
<package-manager> build
git diff --check
```

Adjust commands to match the repository and slice.

Do not run project-wide expensive suites unless the assignment or main coordinating thread requests them.

Report exact commands and whether they passed.

If a check fails, fix failures caused by this slice, then re-run the failed check.

Repeat fix and re-verify until the acceptance criteria pass.

If the same check still fails after three distinct fix attempts, stop retrying and escalate to the coordinator with the attempts tried and their outcomes.

If a failure is pre-existing or outside the slice, report the evidence and leave it for the coordinator.

## Handoff to coordinator

Finish by reporting the slice state back to the main coordinating thread.

Handoff is a review submission, not termination.

Stay available for coordinator review feedback after handoff.

Treat coordinator fix-up direction as continuation of the same slice.

The slice is complete only when the coordinator accepts the handoff against the acceptance criteria.

Before handoff, commit all slice changes on the slice branch and report the branch, worktree path, commit SHAs, and a short diff summary.

Do not open a PR.

Do not push unless the assignment explicitly says to push.

Do not run no-mistakes.

Do not perform merge or post-merge cleanup.

## Final response format

Keep the final response concise and coordinator-friendly.

Include:

- slice status: complete (all acceptance criteria verified), partial (named acceptance criteria unmet), or blocked (waiting on the coordinator);
- slice branch, worktree path, and commit SHAs;
- changed files;
- behavior implemented;
- verification commands and results;
- blockers, failed checks, or unresolved conflicts;
- attention or approval escalations raised and coordinator decisions received;
- cross-slice risks or files likely to conflict with other workers;
- follow-up notes for the main coordinating thread.
