---
name: swarm
description: Use when orchestrating multiple parallel coding slices from a single coordinating thread that dispatches swarm-worker agents into per-slice git worktrees, adjudicates their escalations, reviews their committed diffs against acceptance criteria, and integrates the results into one final PR. Coordinator-only companion to the swarm-worker skill. Never use inside a worker thread; for a single solo slice with full PR workflow use blaze.
---

# Swarm

Use this skill only in the main coordinating thread.

The coordinator decomposes approved scope into slices, dispatches one swarm-worker per slice, keeps two-way communication with every worker, and reviews their work until satisfactory.

The coordinator never implements a slice itself.

Workers follow the `swarm-worker` skill and own nothing beyond their assigned slice.

## Model policy

The coordinator runs on the session model chosen by the user at launch.

Workers run on one uniform worker model or capability tier, chosen once before dispatch from the options the harness's dispatch mechanism actually supports.

Do not pick models per slice unless the user explicitly asks for it.

If the requested worker model or tier is not available in the harness, report that before dispatch instead of silently substituting.

## Branch and worktree layout

Never commit to main or the repository's default branch, in any thread.

Before dispatch, create an integration branch off the base branch, for example `integration/<scope>`.

Create one git worktree with its own slice branch per slice, branched from the integration branch:

```bash
git worktree add ../<repo>-<slice> -b slice/<slice-name> <integration-branch>
```

All slice edits and commits happen in worker worktrees; the coordinator's checkout is for review and integration only.

## Slice decomposition

Break the approved scope into independent slices.

Each slice must satisfy the swarm-worker runnable-slice contract:

- expected behavior;
- key files or areas;
- tests and build checks;
- acceptance criteria phrased as objectively checkable conditions;
- docs or explicit no-docs-needed;
- out-of-scope items;
- any cross-slice constraints.

Prefer slices that touch disjoint files.

When slices must share files, state the shared files and the constraint in every affected assignment.

Sequence a slice behind another only when it strictly requires the other's output.

Present the slice plan to the user and wait for approval before dispatching workers.

## Dispatch

Dispatch one worker per approved slice, in parallel, within the concurrency cap in Stop conditions.

Each assignment must be self-contained and include only that slice's context.

Each assignment must instruct the worker to read and follow the `swarm-worker` skill; name the installed path only when the harness requires an explicit path.

Each assignment must name the worker's worktree path and slice branch and state that all work and commits happen there.

Each assignment must tell the worker to commit its own slice on its slice branch and report the branch and commit SHAs in the handoff.

Do not dispatch a worker before its worktree and slice branch exist.

Each assignment must name the escalation channel: message the coordinating thread and block waiting for the reply.

Each assignment must tell the worker to skip project-wide format, lint, and test suites unless the slice assignment asks for them; targeted formatting and checks on the worker's own changed files stay allowed.

For non-trivial slices, request spec mode: the worker drafts the slice design and submits it over the escalation channel before implementing.

The coordinator runs project-wide verification once at integration.

## Escalation adjudication

Monitor workers and treat any worker message as an escalation to handle promptly.

For each escalation, decide the class:

1. Coordinator-decidable: answer over the message channel with a confirmed next action.
2. Needs human approval: surface the decision to the user, wait, then relay the user's decision back to the worker as the confirmed next action.
3. Cross-worker conflict: pause the affected workers, decide an ordering or boundary, and communicate it to each affected worker.
4. Spec draft submission: review the draft against the slice contract and acceptance criteria, debate within the spec-debate cap in Stop conditions, then confirm implementation start.

Record every escalation and decision for the final report.

Do not leave a worker blocked without a response.

## Stop conditions

A fan-out without stop conditions stalls silently; enforce these throughout the run:

- **Concurrency cap**: dispatch at most as many workers as you can actively monitor; default to 4 concurrent workers and queue the remaining slices, dispatching the next whenever a slot frees up.
- **Worker staleness**: set a staleness threshold per worker at dispatch, scaled to the slice size. A worker silent past the threshold gets one status ping; if it stays silent, treat it as dead, salvage any committed work on its slice branch, and respawn with a tightened assignment in a fresh worktree state.
- **Fix-up cap**: at most three review fix-up rounds per slice; after the third unsatisfactory handoff, stop that slice and escalate to the user with the diffs and evidence.
- **Spec-debate cap**: at most three rounds of spec debate per slice; if consensus is not reached, present both positions to the user as the decision.
- **No-progress halt**: if every active worker is blocked or stale at the same time, stop dispatching, summarize the situation, and escalate to the user instead of waiting indefinitely.

Record every stop-condition trigger and its resolution for the final report.

## Review loop

Review every worker handoff against the slice's acceptance criteria and verification evidence.

Review the committed diff of the slice branch, for example `git diff <integration-branch>...<slice-branch>`, alongside the worker's verification evidence.

If the handoff is unsatisfactory, send targeted fix-up direction back to the same worker and let it continue.

Respawn a worker with a tightened assignment only when the original context is unusable or the worker is dead per Stop conditions.

Repeat until the slice is satisfactory, the fix-up cap in Stop conditions is hit, or the user redirects.

Tell the worker when its handoff is accepted so it can close the slice.

Do not accept confidence statements in place of verification evidence.

## Integration

After all slices are satisfactory:

1. Merge or cherry-pick one slice branch at a time into the integration branch.
2. Run the project-wide test, typecheck, and build commands after each merge.
3. Fix integration failures, or dispatch fixes, before merging the next slice.
4. Resolve merge conflicts manually or dispatch one final integration worker with both slices' context.
5. When every slice is integrated and green, open one final PR from the integration branch following the project's delivery workflow.
6. Remove slice worktrees and delete merged slice branches.

Workers never open PRs, push, or merge.

The coordinator never commits directly to main; delivery happens only through the final PR.

## Final response format

Keep the final response concise.

Include:

- slice table: slice, worker, status, acceptance criteria result;
- escalations raised and decisions made, including user approvals;
- stop-condition triggers (stale workers, capped slices) and how each was resolved;
- integration branch, merge or cherry-pick order, and per-merge verification results;
- final PR link or the reason no PR was opened;
- unresolved conflicts or follow-ups;
- next required user action.
