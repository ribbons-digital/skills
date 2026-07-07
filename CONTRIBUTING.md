# Contributing

Thanks for your interest in improving these skills.
Contributions of all sizes are welcome: fixing wording that steers an agent wrong, adding trigger evals, hardening an existing skill, or proposing a new one.

## The flow

Direct pushes to `main` are blocked by a branch ruleset.
All changes land through a pull request with one approving review and a passing `validate` check.

1. Fork the repo and create a branch.
2. Make your change.
3. Run the validator locally before pushing:

```bash
python3 scripts/validate_skills.py
```

4. Open a PR describing what the change does and why.

## What the validator enforces

Every top-level skill folder must contain:

```
<skill-name>/
  SKILL.md      # frontmatter with name (matching the folder) and description
  README.md     # what it does, install, trigger examples
  evals/
    evals.json  # labelled trigger queries with unique integer ids
```

The repo root must keep `README.md` and `LICENSE`.

## House style

- No em dashes or en dashes anywhere in Markdown; use a plain "-". The validator fails on them.
- In prose, put each full sentence on its own line.
- Skill bodies state rules, not rationale; put the "why" in the skill's README.
- Prefer an escape hatch ("when the situation is not covered, stop and ask") over enumerating edge cases.

## Writing a good skill

- The frontmatter `description` is the trigger: say when to use the skill, when not to, and name sibling skills for the cases it should not handle. Keep it tight; every installed skill pays its description into every session.
- Keep skills harness-agnostic: name capabilities ("run the test suite", "open a PR") rather than harness-specific commands, and offer fallbacks where a primitive may be missing.
- No project-specific paths, file names, or tool assumptions; skills must work across projects.
- Add at least one negative eval: a prompt the skill should NOT fire on.
- If the skill has non-obvious verification behavior, make acceptance criteria objectively checkable.

## Proposing a new skill

Open an issue first describing the failure mode the skill addresses and the artifact it produces.
A skill that does not produce a reviewable outcome (a plan, a spec, a report, a diff) is usually better as part of an existing one.

## License

By contributing, you agree that your contributions are licensed under the repository's [MIT License](LICENSE).
