---
name: loop-architect
description: Use this skill to design an execution loop for a repetitive, long-running, or recurring coding task before running it, including migrations, test/lint burn-downs, bug hunts, CI triage, and dependency updates. Invoke on "design/build a loop", "loop this until done", loop engineering, or when the agent repeats the same change or prompt across 3+ items; pause and propose a loop. Deliverable is a reviewed Loop Card (goal, exit condition, iteration unit, verification, state, stop conditions, human gates), runnable loop prompt, and initialized state. Skip one-shot tasks, already-designed loop runs, and questions about loops in program code.
---

# Loop Architect: Design the Loop, Not the Prompt

When a task needs many similar passes, the leverage is not in any single prompt.
It is in the loop around the prompts: what one iteration does, how it is verified, where state lives, and when it stops.
This skill is a repeatable process for designing that loop once, so the human reviews a loop design instead of hand-typing the next prompt forever.
The engineer's role shifts from "person who prompts" to "person who designs the system that prompts".

Two rules govern everything below.
First, a loop is only as trustworthy as its verifier, and the doer must never grade its own work.
Second, a loop without a machine-checkable exit either runs forever or lies about being done.

## Step 0: Qualify the task

Not every task deserves a loop.
A loop is warranted when the task decomposes into repeatable units of similar shape, has a verifiable done-condition, and each unit can survive a fresh context that knows nothing except external state.
If the task is one-shot, say so and stop: do it directly, or route to planning instead.

If a loop is warranted, classify it into an archetype, because the archetype determines the exit condition and stop conditions:

| Archetype | Shape | Exit condition | Example |
|---|---|---|---|
| **Burn-down** | Finite known work list | List empty | Migrate 80 files to the new API, fix all 40 lint errors |
| **Convergence** | Iterate against a metric | Metric passes threshold | Make the test suite green, hit a perf or coverage target |
| **Discovery** | Unknown-size search | K consecutive empty rounds | Bug hunt, dead-code sweep, flaky-test audit |
| **Watch** | Recurring on trigger or cadence | Never (runs indefinitely) | Nightly CI-failure triage, dependency update check |
| **Pipeline** | Each item flows through stages | All items through final stage | Find issue, then fix, then verify, then open PR |

Qualification and archetype choice require reading the actual repo: run the searches that size the work list now, rather than designing against guesses.
State the archetype to the user in one sentence before designing further.
If the task mixes archetypes (common: discovery feeding a pipeline), design them as separate loops chained by a shared work list.

## Step 1: Define the exit before anything else

Write the done-condition as a check a machine can run, not a vibe.
"All files under src/legacy/ import from @core/v2 and `pnpm test` exits 0" is an exit condition.
"The migration is complete" is not.

For Watch loops, which never exit, define instead the per-run success condition and the cadence.
Distinguish the two loop primitives: cadence-based loops run on an interval regardless of state, while goal-based loops run until the exit check passes.
Picking the wrong primitive is the most common design error: a burn-down on a timer wastes runs after finishing, and a watch loop with a fake "done" never fires again.

## Step 2: Design one iteration

Define the smallest unit of work that produces independently verifiable progress.
Too small and per-iteration overhead (context loading, verification) dominates; too big and a failed iteration loses too much work and cannot be reviewed.
Good default: one file, one failing test, one issue, one finding.

The iteration contract, which the loop prompt must enforce:

1. Read the state file; pick the next pending item.
2. If no pending items remain, run the exit check; on pass, write the final summary and stop; on fail, convert failures into new items and continue.
3. Do the unit of work.
4. Hand the result to verification (Step 3); the doer does not grade itself.
5. Update the state file with the result before doing anything else.
6. Emit a one-line progress report.

Assume every iteration starts with amnesia.
Anything the next iteration needs must be in the state file or the repo, never in conversation memory.

## Step 3: Design verification (the grader)

This is the step that decides whether the loop can run unattended, so spend the most design effort here.
Order graders from cheap-deterministic to expensive-agentic:

1. **Deterministic checks first**: tests, typecheck, lint, build, diff-size limits, forbidden-path guards.
2. **Agentic judge second**, only for what determinism cannot cover: code quality, scope alignment ("did it change only what the item asked?"), convention adherence.
3. **Human last**, reserved for the gates in Step 5.

Separate the creator from the verifier.
The agentic judge must see the diff and the rubric, not the doer's reasoning, otherwise it inherits the doer's blind spots and rubber-stamps them.
Use whatever isolation the harness offers: a sub-agent where available, otherwise a fresh session or a separate model invocation given only the diff and rubric.
Give the judge a written rubric with pass/fail criteria, not "review this"; a self-contained rubric is also what lets a different or weaker model grade reliably.

On verification failure, feed the concrete failure output back into the item's notes and retry once; on second failure, mark the item `blocked` with the evidence and move on.
Blind retries without the failure evidence are the loop equivalent of mashing the same button.

## Step 4: Externalize state

Context dies between iterations; state must live outside it.
Default to a single `loop-state.md` (or `.json` for large lists) at the repo root or scratchpad, containing:

- **Work list**: every item with status `pending | in-progress | done | blocked`, plus per-item notes.
- **Done log**: one line per completed item with what changed.
- **Deviations and findings**: anything discovered mid-loop that changes the plan.
- **Counters**: iteration count, consecutive no-progress count, blocked count.

Rules the loop prompt must state verbatim: read state before acting, write state after every item, never trust memory over the file, and never delete history from the file.
For loops that outlive one machine or one person, promote state to an issue tracker or board instead of a file.

## Step 5: Stop conditions and human gates

Every loop needs hard stops beyond its exit condition, because unattended loops make unattended mistakes:

- **Max iterations**: a ceiling that forces a human check-in even when progressing.
- **Stuck detector**: N consecutive iterations with no `done` transition, or K items going `blocked` in a row, halts the loop.
  A single item failing twice only goes `blocked` per Step 3; it does not halt on its own.
- **Budget**: token or time cap when cost matters.
- **Escalation triggers**: anything irreversible or outward-facing (push, PR merge, deploy, deletion, external API writes) stops the loop and asks, unless the user pre-authorized it explicitly in the Loop Card.

Then place the human deliberately, at one or more of these junctures:

- **Before the loop runs**: approve the Loop Card itself (always required; see Step 7).
- **Inside an iteration**: approve sensitive tool calls or act as the grader for high-stakes items.
- **At the boundary**: review the aggregated done log and blocked list, not every diff.
- **Triage inbox**: blocked items land somewhere the human actually looks, with the evidence attached.

When the loop hits ambiguity the Loop Card does not cover, the rule is escalate, do not improvise.

## Step 6: Trigger and isolation

Choose how iterations are driven:

- **Manual re-run**: the user re-invokes with the loop prompt; simplest, good for first runs, and works in every harness.
- **Interval**: a cadence runner (`/loop 10m <prompt>` in Claude Code, a cron job, a CI schedule, or a shell `while` loop invoking the CLI); right for Watch loops.
- **Self-paced**: the agent schedules its own next iteration, where the harness supports it; right for burn-downs with variable item cost.
- **Event-driven**: webhook, CI failure, new issue; right for triage loops embedded in the ecosystem.
- **Scheduled**: cron or scheduled agents for daily/nightly runs.

Choose isolation to match blast radius: any loop that mutates files runs on a branch or worktree, never the user's working tree; parallel lanes get one worktree each so agents cannot collide.
Grant the narrowest tool permissions the iteration needs, since a loop multiplies whatever access it has.

For high-stakes or ambiguous items, fan out instead of committing to one attempt: dispatch the same item to N parallel lanes (one worktree each, same iteration contract), then have the judge adversarially compare the candidate diffs against the rubric and keep exactly one; the rest are discarded, not merged.
Cost scales by N, so reserve this for items where a plausible-but-wrong fix is expensive to catch later, and record in the state file which candidate won and why.

## Step 7: Assemble the Loop Card and hand off

Fill in the Loop Card and present it to the user for approval before anything runs.
This is the review gate; do not skip it even if the design seems obvious.

```markdown
# Loop Card: <name>

- **Archetype**: burn-down | convergence | discovery | watch | pipeline
- **Goal**: <one sentence>
- **Exit condition**: <machine-runnable check, or cadence for watch loops>
- **One iteration**: <the unit of work>
- **Verification**: <deterministic checks, then judge rubric, in order>
- **State**: <where it lives, what it tracks>
- **Stop conditions**: max <N> iterations; halt after <K> no-progress rounds; <budget>
- **Human gates**: <pre-authorized actions; what escalates; where blocked items go>
- **Trigger**: manual | interval runner (harness loop command, cron, or CI schedule) | self-paced | event | schedule
- **Isolation**: <branch/worktree; tool permissions>
```

After approval, generate the runnable loop prompt from this template, filled with the Card's specifics, and save it next to the state file so the user runs it instead of typing prompts:

```markdown
You are running one iteration of the "<name>" loop. Work strictly from <state-file>.

1. Read <state-file>. Pick the first item with status `pending`; set it `in-progress`.
2. If nothing is pending: run `<exit check>`. If it passes, write a final summary
   to <state-file> and stop with "LOOP DONE". If it fails, add each failure as a
   new pending item and continue.
3. Do the work for this item only: <one-iteration definition>. Touch nothing else.
4. Verify: run <deterministic checks>. Then <judge instruction with rubric>.
   On failure, record the evidence in the item's notes and retry once; on second
   failure, set the item `blocked` with the evidence and move on.
5. Update <state-file>: item status, done log line, counters. Do this before reporting.
6. Report one line: "<n> done / <m> pending / <k> blocked - <what this iteration did>".

Hard stops: halt and escalate if <stuck detector>, if iteration count exceeds <N>,
or before any of: <escalation triggers>. When the situation is not covered by these
instructions, stop and ask; do not improvise.
```

For Watch loops, which have no exit, replace step 2 of the template with: "If nothing is pending, run the per-run success check `<check>`, write results to `<state-file>`, and stop until the next `<cadence>` trigger; never emit LOOP DONE."

Initialize the state file with the work list (for burn-downs, enumerate it now with real searches, not guesses) before declaring the loop ready.
For large work lists, do not authorize the full run at once: pilot 3-5 iterations, then hold a boundary review of the done log, blocked list, and cost before approving the rest.
The pilot doubles as the first Step 8 review; feed its findings back into the Loop Card before the full run.

## Step 8: Hill-climb the loop itself

The loop's failures are the spec for its next version.
After a run (or a batch of iterations), review the done log and blocked list and ask: which failures were loop-design failures rather than task difficulty?
Feed the answers back in: a recurring bad guess becomes a new line in the loop prompt, a class of misses becomes a new rubric criterion or deterministic check, and a repeated escalation becomes either a pre-authorization or a permanent exclusion.
Update the Loop Card version and note what changed, so the loop improves run over run instead of repeating its mistakes.

## Portability across harnesses and models

The loop design stays harness-agnostic when the Loop Card, loop prompt, and state file are plain text in the repo.
The state file, not the harness, is the source of truth across Claude Code, Codex, Cursor, or a bare API script.

- Write the loop prompt with no harness-specific commands or tool names; name the capability ("run the test suite", "search the repo", "open a PR") and let each harness map it to its own tools.
- Do not assume model strength; the iteration contract, rubric, and stop conditions must be explicit enough that a weaker model fails safe (marks items `blocked`) rather than improvising.
- Map missing primitives to fallbacks: no sub-agents means a fresh session acts as judge; no worktrees means one dedicated git branch per lane; no interval runner means cron or manual re-run; no scheduler means a CI schedule.

## Warnings to carry into every design

- **Verification burden stays human at the boundary.** Graders reduce, never eliminate, review; make the boundary review cheap (aggregated logs, small diffs) instead of pretending it is unnecessary.
- **Comprehension debt compounds.** A loop that ships changes the user does not understand is digging a hole; schedule understanding, such as reading the aggregated diff or a post-run quiz, as part of the boundary gate.
- **Cognitive surrender is the real risk.** Design loops to multiply understanding, not to avoid thinking; two identical loops produce opposite outcomes depending on which of these the owner is doing.
