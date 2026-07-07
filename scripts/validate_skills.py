#!/usr/bin/env python3
"""Validate skill folders: frontmatter, naming, evals, and house style.

Run from anywhere: python3 scripts/validate_skills.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".github", "scripts"}

errors = []


def err(msg):
    errors.append(msg)


skill_dirs = [
    d
    for d in sorted(ROOT.iterdir())
    if d.is_dir() and d.name not in SKIP_DIRS and not d.name.startswith(".")
]
if not skill_dirs:
    err("no skill directories found")

for required in ("README.md", "LICENSE"):
    if not (ROOT / required).exists():
        err(f"repo root: missing {required}")

for d in skill_dirs:
    skill = d / "SKILL.md"
    if not skill.exists():
        err(f"{d.name}: missing SKILL.md")
        continue
    text = skill.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        err(f"{d.name}/SKILL.md: missing YAML frontmatter")
        continue
    fm = m.group(1)
    name_m = re.search(r"^name:\s*(\S+)\s*$", fm, re.M)
    desc_m = re.search(r"^description:\s*(.+)$", fm, re.M)
    if not name_m:
        err(f"{d.name}/SKILL.md: frontmatter missing 'name'")
    elif name_m.group(1) != d.name:
        err(
            f"{d.name}/SKILL.md: name '{name_m.group(1)}' does not match folder name"
        )
    if not desc_m or not desc_m.group(1).strip():
        err(f"{d.name}/SKILL.md: frontmatter missing 'description'")
    if not (d / "README.md").exists():
        err(f"{d.name}: missing README.md")
    evals = d / "evals" / "evals.json"
    if not evals.exists():
        err(f"{d.name}: missing evals/evals.json")
    else:
        try:
            data = json.loads(evals.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("top level must be an object")
            if data.get("skill_name") != d.name:
                err(f"{d.name}/evals/evals.json: skill_name does not match folder name")
            items = data.get("evals")
            if not isinstance(items, list) or not items:
                raise ValueError("'evals' must be a non-empty list")
            ids = []
            for e in items:
                if not isinstance(e, dict) or not isinstance(e.get("id"), int):
                    raise ValueError("every eval must be an object with an integer 'id'")
                ids.append(e["id"])
            if len(ids) != len(set(ids)):
                err(f"{d.name}/evals/evals.json: duplicate eval ids")
        except (json.JSONDecodeError, ValueError) as e:
            err(f"{d.name}/evals/evals.json: invalid ({e})")

# House style: plain "-" only, no em or en dashes in markdown.
for md in ROOT.rglob("*.md"):
    rel = md.relative_to(ROOT)
    if any(part in SKIP_DIRS or part.startswith(".") for part in rel.parts[:-1]):
        continue
    for i, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
        if "—" in line or "–" in line:
            err(f"{rel}:{i}: em/en dash found (house style: plain '-')")

if errors:
    print("Skill validation failed:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print(f"OK: {len(skill_dirs)} skills validated")
