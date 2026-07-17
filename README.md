# Skills That Design the Work

Agent skills for the meta-work around coding agents: surfacing what you don't know before the agent guesses, designing the loop instead of being the loop, and running delivery through review gates instead of hope.

Most agent failures are not model failures.
They happen before the first token: an unknown the prompt never surfaced, a human hand-typing the same instruction for the fifteenth time, or a change that shipped without anyone independent ever looking at it.
These skills attack that layer.
Each one is a repeatable process the agent walks through with you, ending in an artifact you review - a plan, a quiz, a Loop Card, a slice spec - instead of vibes.

## Quickstart (30 seconds)

1. Clone or download this repo.

```bash
git clone https://github.com/ribbons-digital/skills.git
```

2. Copy the skills you want into your skills directory:

```bash
# personal (all projects)
cp -R skills/knock-knock skills/loop-architect skills/routine-architect skills/blaze skills/swarm skills/swarm-worker ~/.claude/skills/

# or project-scoped: same, targeting <your-project>/.claude/skills/
```

Take only what you need; each skill is self-contained, except that `swarm` requires `swarm-worker` alongside it.

3. Restart your agent session so the skills are picked up.

4. Invoke the skill you want by name, for example `/knock-knock`, `/loop-architect`, `/routine-architect`, `/blaze`, or `/swarm`.

> [!TIP]
> These skills are plain markdown with minimal frontmatter, so they are not Claude Code specific.
> Codex CLI supports the same skills format (invoke via `$skill-name` or reference from `AGENTS.md`); other harnesses can point a rule at the `SKILL.md` file.

## Why These Skills Exist

### #1: The Agent Guessed What You Meant

The prompt is a map; the codebase and domain are the territory.
Every gap between them gets filled with a guess, and the bigger the task, the more guesses compound.

**The fix:** [knock-knock](knock-knock/SKILL.md) is a process for finding your unknowns - especially the unknown unknowns - before, during, and after the work.
It classifies the task's information into quadrants, then routes to the right technique: blindspot passes for new territory, brainstorms and prototypes for "I'll know it when I see it", one-question-at-a-time interviews for identified gaps, decisions-first implementation plans, and post-build quizzes so you don't merge what you don't understand.

### #2: You Became the Loop

You typed "fix the next failing test" three times and can see a dozen more coming.
The leverage stopped being in any single prompt; it moved to the loop around the prompts, and right now that loop is you.

**The fix:** [loop-architect](loop-architect/SKILL.md) designs the loop once so you review a spec instead of babysitting iterations.
It qualifies whether a loop is warranted, classifies the archetype (burn-down, convergence, discovery, watch, pipeline), and works through exit condition, iteration unit, verification with creator/verifier separation, external state, stop conditions, and human gates.
The deliverable is a Loop Card you approve plus a runnable loop prompt and state file, harness-neutral by construction.
For non-coding recurring work, [routine-architect](routine-architect/SKILL.md) is the sibling skill: it designs routines for digests, inbox triage, vault upkeep, monitoring, and content pipelines where verification depends on grounding checks, idempotent state, reversible write surfaces, and human-gated outbound actions.

> "You design the system that does it instead."
> - Addy Osmani, [Loop Engineering](https://addyosmani.com/blog/loop-engineering/)

### #3: It Shipped Without a Second Pair of Eyes

The agent planned, implemented, reviewed its own work, and opened the PR - all from the same context, sharing the same blind spots at every step.
Confidence statements piled up where verification evidence should have been.

**The fix:** [blaze](blaze/SKILL.md) runs one coding slice through explicit gates: a second-opinion review by an independent model before you approve the plan, implementation only after your approval, verification with exact commands reported, an independent pre-PR review of the diff, and a validation gate before delivery.
The reviewer model is configurable and deliberately different from the model doing the work.

### #4: One Context, Too Much Work

A single agent grinding through a wide change serially is slow, and its context degrades long before the work ends.
Naive parallelism is worse: agents colliding in the same working tree with nobody adjudicating.

**The fix:** [swarm](swarm/SKILL.md) coordinates and [swarm-worker](swarm-worker/SKILL.md) executes.
The coordinator decomposes approved scope into slices with objectively checkable acceptance criteria, dispatches one worker per slice into its own git worktree, adjudicates escalations, enforces stop conditions (concurrency caps, staleness detection, bounded fix-up rounds), reviews every diff, and integrates everything into one final PR.
Workers own exactly one slice, escalate instead of guessing, and never push or merge.

## Reference

### Planning and discovery

- **[knock-knock](knock-knock/SKILL.md)** - manual-only `/knock-knock` skill for surfacing unknowns before they get expensive: blindspot passes, interviews, brainstorms, reference mining, decisions-first plans, implementation notes, and post-build quizzes.

### Loop engineering

- **[loop-architect](loop-architect/SKILL.md)** - manual `/loop-architect` skill for turning repetitive or recurring coding tasks into designed, verifiable, resumable loops.
- **[routine-architect](routine-architect/SKILL.md)** - manual `/routine-architect` skill for turning repetitive non-coding work into designed, verifiable, resumable routines with strict grounding and write-safety gates.

### Review-gated delivery

- **[blaze](blaze/SKILL.md)** - run one solo coding slice from entry gate to post-merge cleanup, with independent model review of the plan and the diff, user approval gates, a validation tail, and PR workflow. The validation tail prefers the third-party [no-mistakes](https://kunchenguid.github.io/no-mistakes/start-here/quick-start/) gate but degrades gracefully without it.

### Parallel orchestration

- **[swarm](swarm/SKILL.md)** - coordinate multiple slices in parallel: decompose, dispatch workers into per-slice worktrees, adjudicate escalations, enforce stop conditions, integrate into one PR. Requires a harness with worker dispatch and two-way worker messaging.
- **[swarm-worker](swarm-worker/SKILL.md)** - execute exactly one assigned slice in a worker thread: verify location, implement only the slice, escalate instead of guessing, commit and hand off. Also runs standalone with the user as coordinator.

They compose: knock-knock defines what "good" looks like for a task, loop-architect turns coding repetition into a machine that produces it repeatedly, routine-architect does the same for non-coding routines, blaze delivers a single slice through gates, and swarm fans the same discipline out across parallel workers.

## Repo structure

Each skill is a self-contained directory:

```
<skill-name>/
  SKILL.md      # the skill itself (frontmatter description + process) - the only required file
  README.md     # what it does, install, trigger examples
  evals/        # labelled trigger queries for tuning the description
```

## Contributing

Changes land through pull requests with a passing `validate` check; see [CONTRIBUTING.md](CONTRIBUTING.md) for the flow, the local validator, and the house style.

## License

[MIT](LICENSE)
