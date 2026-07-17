# routine-architect

A Claude Code / Claude Agent skill that designs recurring routines for non-coding work instead of leaving the human to re-issue the same prompt every morning.
Given a task, it qualifies whether a routine is warranted, classifies the archetype, and walks through the design: exit or cadence, input watermark, iteration unit, verification (structural checks, grounding checks, then a separate judge), external state, stop conditions, reversibility-classed write surfaces, human gates, and trigger.

The deliverable is a **Routine Card** (a one-page spec the user approves before anything runs) plus a **runnable routine prompt** and an initialized state file, so running the routine is a re-invocation rather than fresh prompting each time.

It is the non-coding sibling of [loop-architect](../loop-architect/README.md), self-contained by design.
The shared methodology (exit-first, iteration contract, doer-never-grades-itself, external state, stop conditions, hill-climbing) is duplicated deliberately so each skill works standalone in any harness.
What differs is redesigned, not renamed:

- **Verification** has no test-suite bedrock: structural checks, then grounding checks (fabrication is the dominant failure mode), then an isolated judge, then permanent human sampling.
- **Isolation** has no git undo: write surfaces are classified reversible / soft-reversible / irreversible, with dry-run pilots, staging surfaces, and per-run volume caps.
- **State** adds an idempotency ledger: input watermarks and processed-item IDs so a crashed or repeated run never double-sends or re-files.

## Install

Skills are discovered as directories under a `skills/` folder. Copy this folder to one of:

- **Personal (all projects):** `~/.claude/skills/routine-architect/`
- **Project-scoped:** `<your-project>/.claude/skills/routine-architect/`

```bash
# personal install
cp -R routine-architect ~/.claude/skills/routine-architect
```

Restart Claude Code (or start a new session) so the skill is picked up.
Invoke it explicitly with `/routine-architect`.

Only `SKILL.md` is required; the `evals/` folder is optional and only used for validating the invocation description.

### Other harnesses

The skill is plain markdown with minimal frontmatter, so it ports beyond Claude Code:

- **Codex CLI**: place the folder in its skills directory (or reference `SKILL.md` from `AGENTS.md`) and invoke via `$routine-architect` or implicit triggering.
- **Cursor and others**: add a rule or instruction pointing at `SKILL.md` ("when a non-coding task recurs, follow skills/routine-architect/SKILL.md to design a routine before executing").
- **Anywhere else**: paste `SKILL.md` into context; the process needs no harness features beyond file access, and the "Portability across harnesses and models" section defines fallbacks for missing primitives (connectors, schedulers, sub-agents).

The artifacts the skill produces (Routine Card, routine prompt, state file) are deliberately harness-neutral plain text, so a routine designed in one tool can be run or resumed in another.

## When to invoke it

Prompts like:

- "Every morning, summarize the new posts in the team channel"
- "Design a routine that files my clippings into the knowledge base"
- "I keep asking you to triage my inbox; automate this"
- "Monitor these tickers and give me a weekly sentiment snapshot"
- "Audit my vault for stale notes and keep going until you stop finding them"

Do not invoke it for:

- One-shot tasks ("summarize this article", "draft this email")
- Repetitive coding tasks in a repository (migrations, test or lint burn-downs, CI triage) - that's [loop-architect](../loop-architect/README.md)
- Running an already-designed routine on its schedule (that's the runner, not the drawing board)

## Relationship to loop-architect

Same drawing-board philosophy, different terrain.
loop-architect designs loops whose blast radius is a git branch and whose verifier is a test suite; routine-architect designs routines whose blast radius is other people's inboxes and whose verifier must be built from structural checks, grounding checks, and sampling.
If the work lives in a repo, use loop-architect; if it lives in channels, feeds, mailboxes, or a knowledge base, use this.

## Scope evals

`evals/evals.json` holds labelled queries used to measure whether the `description:` in `SKILL.md` describes the right manual use cases.
If you edit the description, re-run a skill-creator optimization loop to confirm it still describes the intended scope.
