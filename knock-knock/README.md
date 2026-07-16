# knock-knock

A Claude Code / Claude Agent skill that systematically surfaces a user's unknowns - especially unknown unknowns - before, during, and after a task, so prompts match the real territory of the work.

It covers the full lifecycle: pre-build discovery (blindspot passes, interviews, brainstorms, references, implementation plans), mid-build assumption tracking, and post-build comprehension checks (quizzes, pitches for stakeholder buy-in).

## Install

Skills are discovered as directories under a `skills/` folder. Copy this folder to one of:

- **Personal (all projects):** `~/.claude/skills/knock-knock/`
- **Project-scoped:** `<your-project>/.claude/skills/knock-knock/`

```bash
# personal install
cp -R knock-knock ~/.claude/skills/knock-knock
```

Restart Claude Code (or start a new session) so the skill is picked up. It will then appear in the available-skills list and can be invoked explicitly with `/knock-knock`; it is manual-only because `disable-model-invocation: true` is set in frontmatter.

Only `SKILL.md` is required for the skill to work; the `evals/` folder is optional and only used for validating/tuning the trigger description (see below).

## When to invoke it

Prompts like:

- "Do a blindspot pass on this feature before I start"
- "knock-knock this project"
- "Help me find my unknown unknowns for this migration"
- "Interview me about anything ambiguous in this spec before we build"
- "I'll know what I want when I see it"
- "Quiz me on this diff before I merge it"
- "Package this work into a pitch so the team approves it"

Do not invoke it for mechanical tasks (typos, renames, formatting) or simple factual questions.

## Trigger evals

`evals/evals.json` holds labelled queries (`should_trigger: true/false`) used to measure whether the `description:` describes the right manual use cases. The current description was tuned against this set with Anthropic's `skill-creator` optimization loop, scoring 19/20. If you edit the description, re-run the loop to confirm it still describes the intended scope.
