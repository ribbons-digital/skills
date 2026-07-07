---
name: blaze
description: Use when running a solo review-gated coding slice from entry gate to post-merge cleanup, with second-opinion model review of plans and specs, explicit user approval before implementation, verification, pre-PR model review, no-mistakes validation, PR workflow, and branch cleanup. The reviewer model is configurable and defaults to claude-opus-4-8. Not for worker threads dispatched by the swarm coordinator (use swarm-worker) and not for orchestrating multiple parallel slices (use swarm).
---

# Blaze

Use this skill to run a disciplined, review-gated coding slice from entry gate to post-merge cleanup.

## Reviewer model

Every review gate in this skill uses one reviewer model, resolved once at the start:

1. A reviewer model explicitly named in the invocation, for example `/blaze fable` meaning `claude-fable-5`.
2. A reviewer model named in the project's agent instructions.
3. Otherwise the default: `claude-opus-4-8`.

Prefer a reviewer model different from the session model; a second opinion from the same model in a fresh context shares its blind spots.

If the resolved reviewer model is unavailable in the environment, report that and ask the user instead of silently substituting.

## Core posture

Move fast, but do not skip gates.

Keep the active slice small and explicit.

Do not start implementation until the user approves the plan or spec.

Do not invent extra optimization work unless the user asks what else could be improved.

Prefer clear verification evidence over confidence statements.

## Entry gate

Start by identifying the current mode:

1. Research or planning only.
2. Roadmap, spec, or design.
3. Implementation slice.
4. Cleanup or release.
5. Stop and wait.

If the project keeps a status or handoff doc, read it, then verify against repository state.

Check `git status`, current branch, recent commits, and relevant docs before changing files.

## Slice selection and planning gate

When recommending the next slice or drafting a design/spec, get a second opinion from the reviewer model before presenting it to the user.

Write the review prompt to a scratch file first, containing everything the reviewer needs to judge standalone: the proposal or spec, the goal and constraints, and the verdict format expected back.

Invoke the reviewer with:

```bash
claude --model <reviewer-model> -p "$(cat <scratch-file>)"
```

Do not paste specs or diffs inline into a quoted `-p` string; shell quoting breaks silently on real content.

Do not use a subagent, alternate model, or model alias for this review.

If the command fails, stop and report the failure instead of claiming review happened.

Each `-p` call is stateless, so every debate round's scratch file must restate the prior rounds' positions.

Debate tradeoffs with the reviewer until there is a consensus, for at most three rounds; if disagreement remains, present both positions to the user as the decision.

Then present the consensus recommendation/spec to the user for approval.

## Implementation gate

After user approval, create a feature branch unless already on the correct feature branch.

Define the slice before editing:

- expected behavior;
- key files or areas;
- tests and build checks;
- docs or explicit no-docs-needed;
- out-of-scope items.

Implement only the approved slice.

Park valuable new ideas as follow-ups instead of switching focus.

## Verification

Run the narrowest meaningful checks first.

Then run broader checks appropriate for the repo.

Use the repository's package manager and instructions.

Typical verification includes:

```bash
<package-manager> test
<package-manager> typecheck
<package-manager> build
git diff --check
```

Adjust commands to match the repository.

Report exact commands and whether they passed.

## Pre-PR implementation review

Before opening a PR, have the reviewer model inspect the completed implementation.

Write the review prompt to a scratch file containing the full diff (`git diff <base-branch>...HEAD`), the approved slice definition, and the verdict format expected back, then invoke:

```bash
claude --model <reviewer-model> -p "$(cat <scratch-file>)"
```

Do not use a subagent, alternate model, or model alias for this review.

Resolve blockers.

If needed, re-review until there is consensus, capped at three rounds; each round's scratch file restates the prior rounds' positions, and remaining disagreements go to the user.

## Validation tail

After the code review is resolved, commit the slice on the feature branch and run the delivery validation gate.

The preferred gate is no-mistakes: load the no-mistakes skill and follow its own runbook for setup, runs, and gate responses; do not duplicate its CLI mechanics from memory, since the skill is the authoritative source for its current commands.

If skill discovery does not surface no-mistakes, its official quick start is the bootstrap reference: https://kunchenguid.github.io/no-mistakes/start-here/quick-start/

Invariants that hold regardless of the runbook version:

- Never push to `main` manually; delivery happens through the validated PR.
- Never install tooling without consent: if the no-mistakes CLI is missing, ask the user before running any install script, and use the fallback below if they decline.
- Use long timeouts for validation runs and responses; review, test, and CI steps can each take several minutes.
- Escalate `ask-user` findings to the user unless the user gave explicit unattended consent.
- Drive the run to a terminal outcome; when checks pass, stop driving the pipeline and ask the user to review and merge the PR.
- If no-mistakes cannot start or is blocked, report the exact command, output, and failure instead of pretending the gate ran.

Fallback when no-mistakes is unavailable or the user declines install:

1. Run the project-wide verification suite (test, typecheck, build, lint) and report the results.
2. With the user's approval, push the feature branch and open the PR following the project's conventions.
3. State plainly in the final response that validation ran without the no-mistakes gate.

## Post-merge cleanup

After the user says the PR was merged:

1. Fetch and fast-forward `main`.
2. Delete the local feature branch.
3. Delete the remote feature branch if it still exists.
4. Clean up no-mistakes gate branches when relevant.
5. Confirm no-mistakes outcome when available.
6. Save a concise checkpoint in the project's status or handoff doc when one exists.

Sync relevant status docs before calling a phase, release, merge, or next-work recommendation complete.

## Final response format

Keep the final response concise.

Include:

- changed files or PR link;
- verification evidence;
- review gate result (including the reviewer model used);
- no-mistakes result when used;
- next required user action.
