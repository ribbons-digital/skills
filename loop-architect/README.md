# loop-architect

A Claude Code / Claude Agent skill that designs the execution loop for a coding task instead of leaving the human to re-type prompts manually.
Given a task, it qualifies whether a loop is warranted, classifies the loop archetype, and walks through the design: exit condition, iteration unit, verification (deterministic checks plus a separate judge), external state, stop conditions, human gates, trigger, and isolation.

The deliverable is a **Loop Card** (a one-page spec the user approves before anything runs) plus a **runnable loop prompt** and an initialized state file, so running the loop is a re-invocation rather than fresh prompting each time.

It synthesizes two references:

- [Loop Engineering](https://addyosmani.com/blog/loop-engineering/) by Addy Osmani: the shift from prompting to designing the system that prompts, the component toolbox (automations, worktrees, skills, connectors, sub-agents, external state), and the warnings about verification burden, comprehension debt, and cognitive surrender.
- [The Art of Loop Engineering](https://www.langchain.com/blog/the-art-of-loop-engineering) by LangChain: the four-loop stack (agent loop, verification loop, event-driven loop, hill-climbing loop), grader design, and human-in-the-loop placement.

## Install

Skills are discovered as directories under a `skills/` folder. Copy this folder to one of:

- **Personal (all projects):** `~/.claude/skills/loop-architect/`
- **Project-scoped:** `<your-project>/.claude/skills/loop-architect/`

```bash
# personal install
cp -R loop-architect ~/.claude/skills/loop-architect
```

Restart Claude Code (or start a new session) so the skill is picked up.
It will then trigger automatically on relevant prompts, or you can invoke it explicitly with `/loop-architect`.

Only `SKILL.md` is required; the `evals/` folder is optional and only used for validating the trigger description.

### Other harnesses

The skill is plain markdown with minimal frontmatter, so it ports beyond Claude Code:

- **Codex CLI**: Codex supports the same skills format; place the folder in its skills directory (or reference `SKILL.md` from `AGENTS.md`) and invoke via `$loop-architect` or implicit triggering.
- **Cursor and others**: add a rule or instruction pointing at `SKILL.md` ("when a task is repetitive across many items, follow skills/loop-architect/SKILL.md to design a loop before executing").
- **Anywhere else**: paste `SKILL.md` into context; the process needs no harness features beyond file access, and the section "Portability across harnesses and models" defines fallbacks for missing primitives (sub-agents, worktrees, interval runners).

The artifacts the skill produces (Loop Card, loop prompt, state file) are deliberately harness-neutral plain text, so a loop designed in one tool can be run or resumed in another.

### Proactive triggering

The skill's description also fires proactively: when the agent notices it is repeating the same shape of change or prompt across 3+ items, it should pause and propose a loop.
Skill descriptions alone catch this unreliably, so pair it with an always-on rule in your global instructions (CLAUDE.md / AGENTS.md), for example:

> If you notice yourself making the same shape of change, fix, or prompt across 3 or more items in a session, pause and propose designing a loop for it (use the loop-architect skill if available) instead of continuing item by item.

## What triggers it

Prompts like:

- "Design a loop to migrate all 80 files off the legacy API"
- "I keep re-prompting you to fix the next failing test; build me a loop for this"
- "Set up an autonomous loop that burns down our lint errors"
- "Help me loop-engineer a nightly CI triage"
- "Turn this bug-hunt into a loop that runs until it stops finding things"

It intentionally does **not** trigger for:

- One-shot tasks ("fix this bug", "add this endpoint")
- Running an already-designed loop on an interval (that's `/loop`)
- Loops in program code ("why does this for loop never exit", React render loops)
- Non-coding recurring work (channel digests, inbox triage, vault upkeep) - that's [routine-architect](../routine-architect/README.md)

## Relationship to /loop

`/loop` is the engine; `loop-architect` is the drawing board.
This skill produces the loop prompt, state file, and stop conditions that make an interval or goal-based runner like `/loop` safe and useful.

## Trigger evals

`evals/evals.json` holds labelled queries used to measure whether the `description:` in `SKILL.md` fires on the right prompts.
If you edit the description, re-run a skill-creator optimization loop to confirm it still triggers correctly.
