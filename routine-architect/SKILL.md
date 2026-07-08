---
name: routine-architect
description: Use this skill to design a recurring routine for non-coding work before running it. Invoke when the user wants to turn repetitive non-coding work into an autonomous routine (daily digests, inbox or channel triage, news or market monitoring, knowledge-base or vault upkeep, content pipelines, data hygiene in external tools), asks to "design a routine", "automate this workflow", "do this every morning/day/week", or keeps manually re-issuing the same non-coding prompt. Also invoke proactively, without being asked, when the agent notices the same non-coding request recurring across 3 or more sessions or items - pause and propose a routine before continuing item by item. For repetitive coding tasks in a repository (migrations, test or lint burn-downs, CI triage), use loop-architect instead. The deliverable is a reviewed Routine Card (goal, exit or cadence, iteration unit, verification, state, stop conditions, human gates, trigger, write surfaces) plus a runnable routine prompt.
---

# Routine Architect: Design the Routine, Not the Prompt

When non-coding work recurs, the leverage is not in any single prompt.
It is in the routine around the prompts: what one run does, how its output is verified, where state lives, what it is allowed to touch, and when it stops.
This skill is a repeatable process for designing that routine once, so the human reviews a routine design instead of re-typing the same request every morning.

Three rules govern everything below.
First, a routine is only as trustworthy as its verifier, and the doer must never grade its own work.
Second, a routine without a machine-checkable exit or per-run success condition either runs forever or lies about being done.
Third, and specific to non-coding work: there is no git to undo a mistake, so every write must be classified by reversibility before the routine is allowed to make it, and fabrication - not bugs - is the dominant failure mode to design against.

## Step 0: Qualify the task

Not every task deserves a routine.
A routine is warranted when the work recurs in similar shape, has a verifiable success condition, and each run can survive a fresh context that knows nothing except external state.
If the task is one-shot, say so and stop: do it directly.
If the task is repetitive coding work in a repository, route to loop-architect instead; this skill covers work whose inputs and outputs live outside a codebase.

If a routine is warranted, classify it into an archetype, because the archetype determines the exit condition and stop conditions:

| Archetype | Shape | Exit condition | Example |
|---|---|---|---|
| **Burn-down** | Finite known work list | List empty | Re-tag 200 mislabeled vault notes, process a clippings backlog |
| **Convergence** | Iterate against a metric | Metric passes threshold | Deduplicate a knowledge base until duplicate rate is under 2% |
| **Discovery** | Unknown-size search | K consecutive empty rounds | Audit for stale or contradictory notes, find broken links, subscription audit |
| **Watch** | Recurring on trigger or cadence | Never (runs indefinitely) | Morning channel digest, news or market monitoring, weekly sentiment snapshot |
| **Pipeline** | Each item flows through stages | All items through final stage | Clip, then summarize, then tag, then file into the knowledge base |

Non-coding work is watch-dominant: most routines have no exit, only a cadence and a per-run success condition.
Qualification requires enumerating the real inputs now - query the actual source (API, folder, feed, mailbox) to size the work rather than designing against guesses.
State the archetype to the user in one sentence before designing further.
If the task mixes archetypes (common: a watch feeding a pipeline), design them as separate routines chained by a shared work list.

## Step 1: Define the exit or the cadence before anything else

Write the done-condition as a check a machine can run, not a vibe.
"Every note under Clippings/ has status: processed in its frontmatter and the broken-link check returns zero" is an exit condition.
"The vault is tidy" is not.

For Watch routines, which never exit, define instead the per-run success condition, the cadence, and the input watermark: the marker (last-seen message ID, last-processed timestamp, last item URL) that separates already-handled input from new input.
Match the cadence to how often the source actually changes; a routine that runs hourly against a daily feed wastes most of its runs.
Picking the wrong primitive is the most common design error: a burn-down on a timer wastes runs after finishing, and a watch routine with a fake "done" never fires again.

## Step 2: Design one iteration

Define the smallest unit of work that produces independently verifiable output.
Good default: one message thread, one note, one article, one inbox item, one report.

The iteration contract, which the routine prompt must enforce:

1. Read the state file; pick the next pending item, or pull new input past the watermark.
2. If nothing is pending and no new input exists, run the exit check (or per-run success check for watch routines); on pass, write the summary and stop; on fail, convert failures into new items and continue.
3. Do the unit of work.
4. Hand the result to verification (Step 3); the doer does not grade itself.
5. Update the state file - item status, watermark, processed-item IDs - before any outbound write.
6. Emit a one-line progress report.

Assume every iteration starts with amnesia.
Anything the next iteration needs must be in the state file or the external system, never in conversation memory.

Iterations must be idempotent against re-runs.
In coding, re-applying a migration to an already-migrated file is a no-op; in non-coding, re-processing the same input means a duplicate digest, a double-sent email, or a re-filed note.
The state file's processed-item IDs and watermark are what make a crashed or repeated run safe, so updating them before the outbound write is non-negotiable.

## Step 3: Design verification (the grader)

This is the step that decides whether the routine can run unattended, so spend the most design effort here.
There is no test suite to lean on, so the deterministic bedrock is thinner and the grader hierarchy matters more:

1. **Structural checks first**: schema and frontmatter validation, required fields present, links resolve, dates parse, counts and thresholds met, duplicate detection, output length and format limits.
2. **Grounding checks second**, because fabrication is the dominant failure mode: every factual claim in generated output must carry a source reference that actually resolves, and quoted material must appear in the source.
   A digest that invents a plausible headline passes every structural check; only grounding catches it.
3. **Agentic judge third**, in isolation, for what the above cannot cover: faithfulness to source, completeness, tone, scope alignment ("did it summarize only the new items?").
   The judge sees the output, the source material, and a written pass/fail rubric - never the doer's reasoning.
4. **Human sampling last**: with no test suite, human spot-checks stay load-bearing indefinitely; keep them cheap by sampling a fixed fraction of outputs per boundary review rather than reading everything.

On verification failure, feed the concrete failure back into the item's notes and retry once; on second failure, mark the item `blocked` with the evidence and move on.
Blind retries without the failure evidence are the routine equivalent of mashing the same button.

## Step 4: Externalize state

Context dies between runs; state must live outside it.
Default to a single `routine-state.md` (or `.json` for large lists) in the workspace, vault, or wherever the routine's outputs live, containing:

- **Watermark**: the last-processed input marker, updated before any outbound write.
- **Processed-item IDs**: the idempotency ledger; never process an ID already listed.
- **Work list**: every item with status `pending | in-progress | done | blocked`, plus per-item notes.
- **Run log**: one line per run with timestamp, items handled, and outcome.
- **Deviations and findings**: anything discovered mid-run that changes the plan.
- **Counters**: run count, consecutive no-progress count, blocked count.

Rules the routine prompt must state verbatim: read state before acting, write state after every item, never trust memory over the file, and never delete history from the file.
For routines that outlive one machine or one person, promote state to a tracker or shared document instead of a file.

## Step 5: Stop conditions and human gates

Every routine needs hard stops beyond its exit condition, because unattended routines make unattended mistakes, and non-coding mistakes ship to humans:

- **Max iterations per run**: a ceiling that forces a check-in even when progressing.
- **Stuck detector**: N consecutive runs with no progress, or K items going `blocked` in a row, halts the routine.
- **Volume caps**: a hard maximum on outbound writes per run (messages sent, notes filed, records changed); a runaway routine spamming a channel is the non-coding equivalent of a force-push.
- **Freshness skip**: if the input source has not changed since the watermark, end the run without doing anything; never reprocess to look busy.
- **Budget**: token or time cap when cost matters.

Then classify every write surface by reversibility, because this replaces the branch/worktree safety net that coding loops get for free:

| Class | Examples | Policy |
|---|---|---|
| **Reversible** | Draft folders, staging files, unsent drafts | Routine may write freely |
| **Soft-reversible** | Editable posts, movable or re-taggable notes, tracker comments | Routine may write; boundary review covers them |
| **Irreversible** | Sent messages or emails, deletions, external API writes, notifications to humans | Always gates on a human, unless pre-authorized in the Routine Card for a specific surface with a capped count |

Place the human deliberately: approving the Routine Card (always required; see Step 7), acting as the gate for irreversible writes, reviewing the sampled outputs and blocked list at the boundary, and owning the triage inbox where blocked items land with evidence attached.
When the routine hits ambiguity the Routine Card does not cover, the rule is escalate, do not improvise.

## Step 6: Trigger and isolation

Choose how runs are driven:

- **Manual re-run**: the user re-invokes with the routine prompt; simplest, and correct for the first runs.
- **Interval or schedule**: a cadence runner, cron job, or scheduled agent; right for watch routines - match the interval to the source's change rate.
- **Event-driven**: webhook, new message, new file in a folder; right for triage routines embedded in an ecosystem.

Choose isolation to match blast radius.
There is no worktree to throw away, so isolation means controlling where output lands:

- **Dry-run first**: early runs write a "would have done" report to the state file instead of touching the real surface; the user reviews it before live writes are enabled.
- **Staging surfaces**: write to a drafts folder, a staging note, or a sandbox account, and promote to the real surface only at a human gate or after the routine has earned trust.
- **Narrowest permissions**: grant only the connectors and scopes one run needs, since a routine multiplies whatever access it has; prefer read-only credentials plus a single write surface.

For high-stakes outputs, fan out instead of committing to one attempt: produce N candidate drafts, have the isolated judge compare them against the rubric and keep exactly one, and record in the state file which candidate won and why.
Cost scales by N, so reserve this for outputs where a plausible-but-wrong result is expensive, such as anything outbound to other people.

## Step 7: Assemble the Routine Card and hand off

Fill in the Routine Card and present it to the user for approval before anything runs.
This is the review gate; do not skip it even if the design seems obvious.

```markdown
# Routine Card: <name>

- **Archetype**: burn-down | convergence | discovery | watch | pipeline
- **Goal**: <one sentence>
- **Exit / cadence**: <machine-runnable check, or cadence plus per-run success condition>
- **Input source**: <where items come from; the watermark that marks progress>
- **One iteration**: <the unit of work>
- **Verification**: <structural checks, grounding checks, judge rubric, human sampling rate>
- **State**: <where it lives; watermark, processed IDs, work list, run log>
- **Write surfaces**: <each surface with its reversibility class and per-run volume cap>
- **Stop conditions**: max <N> iterations per run; halt after <K> no-progress runs; <budget>
- **Human gates**: <pre-authorized irreversible writes with caps; what escalates; where blocked items go>
- **Trigger**: manual | interval or schedule | event
```

After approval, generate the runnable routine prompt from this template, filled with the Card's specifics, and save it next to the state file so the user runs it instead of typing prompts:

```markdown
You are running one run of the "<name>" routine. Work strictly from <state-file>.

1. Read <state-file>. Pull new input past the watermark <watermark>; add each new
   item as `pending`. Pick the first `pending` item; set it `in-progress`.
2. If nothing is pending and no new input exists: run <exit or per-run success check>,
   write the run log line, and stop. For watch routines never emit ROUTINE DONE;
   for finite routines emit "ROUTINE DONE" only when <exit check> passes.
3. Do the work for this item only: <one-iteration definition>. Touch nothing else.
4. Verify: run <structural checks>. Check grounding: <grounding rule>. Then
   <judge instruction with rubric>. On failure, record the evidence in the item's
   notes and retry once; on second failure, set the item `blocked` and move on.
5. Update <state-file>: watermark, processed IDs, item status, run log, counters.
   Do this BEFORE any outbound write.
6. Write output only to <write surfaces>, respecting the volume cap of <cap>.
   Anything irreversible not pre-authorized in the Routine Card: stop and ask.
7. Report one line: "<n> done / <m> pending / <k> blocked - <what this run did>".

Hard stops: halt and escalate if <stuck detector>, if this run exceeds <N> items,
or before any of: <escalation triggers>. When the situation is not covered by these
instructions, stop and ask; do not improvise.
```

Initialize the state file with the watermark and, for burn-downs, the enumerated work list (query the real source now, not guesses) before declaring the routine ready.
The first runs are the pilot: run 3-5 iterations in dry-run mode, then hold a boundary review of the would-have-done report, blocked list, and cost before enabling live writes and the full cadence.
The pilot doubles as the first Step 8 review; feed its findings back into the Routine Card before going live.

## Step 8: Hill-climb the routine itself

The routine's failures are the spec for its next version.
After a batch of runs, review the run log and blocked list and ask: which failures were routine-design failures rather than task difficulty?
Feed the answers back in: a recurring bad summary becomes a new rubric criterion, a class of misses becomes a new structural or grounding check, and a repeated escalation becomes either a pre-authorization with a cap or a permanent exclusion.
Update the Routine Card version and note what changed, so the routine improves run over run instead of repeating its mistakes.

## Portability across harnesses and models

The routine design is harness-agnostic by construction: the Routine Card, the routine prompt, and the state file are plain text, so the same routine runs under any agent harness and can switch harnesses mid-stream because the state file, not the harness, is the source of truth.
Keep it that way:

- Write the routine prompt with no harness-specific commands or connector names; name the capability ("read the channel", "fetch the feed", "file the note") and let each harness map it to its own tools.
- Do not assume model strength; the iteration contract, rubric, and stop conditions must be explicit enough that a weaker model fails safe (marks items `blocked`) rather than improvising.
- Map missing primitives to fallbacks: no connector means the user exports input to a folder the routine reads; no scheduler means cron or manual re-run; no sub-agents means a fresh session acts as judge.

## Warnings to carry into every design

- **Verification burden stays human at the boundary, permanently.** Coding loops graduate to trusting their test suite; non-coding routines never fully graduate, because there is no equivalent bedrock. Budget the sampling review as a standing cost, not a temporary one.
- **Silent wrongness compounds.** A fabricated fact filed into a knowledge base today poisons every future retrieval that touches it; this is why grounding checks outrank the judge in Step 3.
- **Outbound mistakes have an audience.** A bad commit embarrasses you in review; a bad email embarrasses you in someone's inbox. Reversibility classes and volume caps exist because the blast radius includes other people.
- **Cognitive surrender is the real risk.** Design routines to multiply attention, not to avoid it; a digest you never read is a routine that should be turned off.
