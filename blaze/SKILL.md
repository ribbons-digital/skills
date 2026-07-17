---
name: blaze
description: Use when running a solo review-gated coding slice from entry gate to post-merge cleanup, with second-opinion model review of plans and specs, explicit user approval before implementation, verification, pre-PR model review, no-mistakes validation, PR workflow, and branch cleanup. Bug fixes follow a reproduce-first path with diagnosis review and a required regression test, with an opt-in quickfix mode for small obvious bugs. The reviewer model is configurable and defaults to claude-opus-4-8. Not for worker threads dispatched by the swarm coordinator (use swarm-worker) and not for orchestrating multiple parallel slices (use swarm).
disable-model-invocation: true
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

## Bug-fix path

When the slice is a bug fix, the gates below adapt as follows; everything else in this skill still applies.

Reproduce before diagnosing: produce a failing reproduction in a setting as close to how the end user experiences the bug as possible, end to end, before proposing any fix.

Create the feature branch up front for a bug fix, since reproduction and diagnosis work precede the user approval that normally gates branch creation; never investigate on `main`.

No reproduction, no fix: if the bug cannot be reproduced, report what was tried and ask the user for more signal instead of fixing blind.

The planning gate reviews the diagnosis, not a spec: the reviewer's scratch file contains the reproduction, the root-cause claim with evidence, and the proposed fix approach, and the reviewer's question is whether the root cause is proven or the fix patches a symptom.

After the diagnosis review, present the diagnosis and fix approach to the user for approval before implementing, exactly as the planning gate requires for a spec.

Acceptance criteria are fixed before implementing: the reproduction passes after the fix, the reproduction graduates into the test suite as a regression test, and the relevant suite stays green.

Keep the fix minimal: fix the cause, not every smell near it, and park refactors as follow-ups.

### Quickfix mode

For small, obvious bugs, the user may opt into quickfix mode with `/blaze quickfix` or equivalent wording.
Treat that invocation as explicit user consent for quickfix mode, but do not leave it implicit: every Quickfix diagnosis, slice definition, handoff, and reviewer prompt must include `Mode: quickfix` and the exact user invocation text that authorized it.
This prevents advisors or reviewers with compressed context from downgrading the run back to full blaze because they only see `/blaze`.

Quickfix mode is allowed only when all of these are true:

- The bug is reproducible in one narrow scenario.
- The root cause is visible from the reproduction.
- The fix is expected to touch at most 1-2 files.
- The change does not affect security, auth, payments, data loss, migrations, concurrency, or cross-system behavior.
- A regression test or narrow verification can prove the behavior.

Quickfix mode keeps the bug-fix invariants: create a branch before investigation, reproduce before fixing, no reproduction means no fix, add or update a regression test when practical, run the narrow relevant verification, and report exact evidence.

Quickfix mode skips the separate diagnosis-review gate and replaces it with an inline Quickfix diagnosis containing reproduction, failing evidence, root cause, minimal fix, and regression check.

If the diagnosis becomes uncertain, the touched area grows, or the verification cannot prove the behavior, stop and fall back to the full bug-fix path.

By default, quickfix mode keeps the pre-PR implementation review but skips no-mistakes unless the user asks for full delivery validation.
If the user explicitly asks to skip the implementation review too, report that blaze ran in local quickfix mode and list the verification that replaced it.
When quickfix mode skips no-mistakes, state `no-mistakes: skipped by quickfix mode` in the slice summary and final response; if any reviewer or advisor claims quickfix was not authorized, compare against the recorded invocation text before changing mode.

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

If skill discovery does not surface no-mistakes, or any no-mistakes command fails in a way its skill does not explain, fetch and follow the official quick start before reporting failure: https://kunchenguid.github.io/no-mistakes/start-here/quick-start/

One bootstrap fact stays here because agents repeatedly failed without it: a validation run is created by the gate's post-receive hook when a push updates a ref on the gate remote, while `no-mistakes axi run` only attaches to a run that already exists.

On an error like `no run started for "<branch>": no previous run for branch`, walk this recovery ladder in order.
After each rung, probe with `no-mistakes axi status` to see whether the daemon registered a run for the branch; attach with `axi run` only once a run exists.
A missing run means move to the next rung, not another `axi run` retry.

1. Push the branch through the gate remote: `git push no-mistakes <branch>`.
2. If that push reports `up-to-date`, it updated no ref, fired no hook, and started nothing, even though the branch is visible in `git ls-remote no-mistakes`; force a ref update by deleting and re-pushing the gate branch: `git push no-mistakes --delete <branch> && git push no-mistakes <branch>`.
3. If a ref-updating push still yields no run, suspect the daemon: run `no-mistakes doctor`, then re-run `no-mistakes init` from the repo root (documented as safe to re-run; it repairs gate wiring and ensures the daemon is running), then push again.
4. If the CLI banner reports a newer version while the gate misbehaves, include that in the report and ask the user before updating; never update the tool on your own.

If no run appears after the full ladder, stop driving the gate and go to the reporting invariant and fallback below.

If the loaded no-mistakes skill or the quick start shows different commands, those win over this fact.

Invariants that hold regardless of the runbook version:

- Never push to `main` manually; delivery happens through the validated PR.
- Never install tooling without consent: if the no-mistakes CLI is missing, ask the user before running any install script, and use the fallback below if they decline.
- Use long timeouts for validation runs and responses; review, test, and CI steps can each take several minutes.
- Escalate `ask-user` findings to the user unless the user gave explicit unattended consent.
- Drive the run to a terminal outcome; when checks pass, stop driving the pipeline and ask the user to review and merge the PR.
- If no-mistakes cannot start after the full recovery ladder and a quick-start consultation, report the exact command, output, and failure instead of pretending the gate ran; a run blocked by its own gate findings is not a start failure, so fix or escalate those findings instead.

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
- review gate result, including reviewer model used, or the explicit reason the gate was skipped;
- no-mistakes result when used;
- next required user action.
