# blaze

A review-gated solo coding skill that runs one slice from entry gate to post-merge cleanup: second-opinion model review of the plan, explicit user approval before implementation, verification, pre-PR model review, a delivery validation gate, and branch cleanup.

The reviewer model is configurable: an invocation argument (`/blaze fable`), a project-level setting, or the default `claude-opus-4-8`, with a preference for a reviewer different from the session model.

## Install

Copy this folder into your skills directory:

```bash
cp -R blaze ~/.claude/skills/blaze     # or <project>/.claude/skills/blaze
```

Restart the session so the skill is picked up, then invoke it explicitly with `/blaze`.

## Dependencies

- The `claude` CLI must be on PATH for the reviewer gates.
- The validation tail prefers the third-party [no-mistakes](https://kunchenguid.github.io/no-mistakes/start-here/quick-start/) skill and CLI, but degrades gracefully: if it is unavailable and the user declines install, blaze falls back to project-wide verification plus a user-approved manual PR.

## When to invoke it

- "Recommend the next slice and draft the spec"
- "Plan approved, implement it with review gates"
- "Fix this bug properly, reproduce it first and ship the fix through the gates"
- "/blaze quickfix - the checkbox toggle is inverted; reproduce it and patch the minimal cause"
- "Implementation is done, run the review and ship the PR"
- "The PR was merged, clean up"

Bug fixes follow a dedicated path: reproduce first, diagnosis review instead of spec review, and the reproduction becomes a required regression test.
Small obvious bugs may use opt-in quickfix mode, which keeps reproduction, branch safety, regression evidence, and narrow verification while replacing the separate diagnosis-review gate with an inline Quickfix diagnosis.
Quickfix mode records the exact `/blaze quickfix` invocation in handoffs and reviewer prompts so advisors do not mistake it for full blaze.

Do not invoke it inside swarm-worker threads or to orchestrate multiple parallel slices; use `swarm-worker` or `swarm` instead.

## Family

`blaze` (solo, full workflow) / `swarm` (coordinator) / `swarm-worker` (dispatched worker).

## Scope evals

`evals/evals.json` holds labelled queries for validating the invocation description; re-run a skill-creator optimization loop after editing the description.
