#!/usr/bin/env python3
"""Validate skill folders: frontmatter, naming, evals, and house style.

Run from anywhere: python3 scripts/validate_skills.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".github", "scripts", "evals", "tests", "eval-workspace"}
MAX_DESCRIPTION_CHARS = 1024

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

known_eval_ids = {}

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
    elif len(desc_m.group(1).strip()) > MAX_DESCRIPTION_CHARS:
        err(
            f"{d.name}/SKILL.md: description exceeds {MAX_DESCRIPTION_CHARS} characters "
            f"({len(desc_m.group(1).strip())})"
        )
    elif ": " in desc_m.group(1).strip():
        err(
            f"{d.name}/SKILL.md: description contains ': ', which breaks plain YAML scalars"
        )
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
                if not isinstance(e.get("prompt"), str) or not e["prompt"].strip():
                    raise ValueError(f"eval {e['id']} must have a non-empty prompt")
                if not isinstance(e.get("expected_output"), str) or not e["expected_output"].strip():
                    raise ValueError(f"eval {e['id']} must have a non-empty expected_output")
                if not isinstance(e.get("files"), list):
                    raise ValueError(f"eval {e['id']} files must be a list")
                assertions = e.get("assertions")
                if not isinstance(assertions, list) or not assertions:
                    raise ValueError(f"eval {e['id']} must have assertions")
                for assertion in assertions:
                    if not isinstance(assertion, dict) or not isinstance(assertion.get("text"), str) or not assertion["text"].strip():
                        raise ValueError(f"eval {e['id']} has an invalid assertion")
                    if assertion.get("type") not in {"behavioral"}:
                        raise ValueError(f"eval {e['id']} has an unsupported assertion type")
            if len(ids) != len(set(ids)):
                err(f"{d.name}/evals/evals.json: duplicate eval ids")
            known_eval_ids[d.name] = set(ids)
        except (json.JSONDecodeError, ValueError) as e:
            err(f"{d.name}/evals/evals.json: invalid ({e})")

smoke_suite = ROOT / "evals" / "smoke-suite.json"
if not smoke_suite.exists():
    err("repo root: missing evals/smoke-suite.json")
else:
    try:
        suite = json.loads(smoke_suite.read_text(encoding="utf-8"))
        cases = suite.get("cases")
        if suite.get("schema_version") != 1 or not isinstance(cases, list) or not cases:
            raise ValueError("schema_version must be 1 and cases must be non-empty")
        selected = []
        for case in cases:
            if not isinstance(case, dict) or not isinstance(case.get("skill"), str) or not isinstance(case.get("eval_id"), int):
                raise ValueError("every smoke case must name a skill and integer eval_id")
            pair = (case["skill"], case["eval_id"])
            selected.append(pair)
            if case["skill"] not in known_eval_ids or case["eval_id"] not in known_eval_ids[case["skill"]]:
                raise ValueError(f"unknown eval reference {case['skill']}:{case['eval_id']}")
            for field in ("slug", "observable_contract", "fixture", "isolation"):
                if not isinstance(case.get(field), str) or not case[field].strip():
                    raise ValueError(f"{case['skill']}:{case['eval_id']} missing {field}")
            for field in ("safety_critical", "deterministic", "qualitative", "required_evidence"):
                if not isinstance(case.get(field), list):
                    raise ValueError(f"{case['skill']}:{case['eval_id']} {field} must be a list")
        if len(selected) != len(set(selected)):
            raise ValueError("duplicate smoke case references")
    except (json.JSONDecodeError, ValueError) as e:
        err(f"evals/smoke-suite.json: invalid ({e})")

results_dir = ROOT / "evals" / "results"
for result_file in sorted(results_dir.glob("*.json")):
    try:
        result = json.loads(result_file.read_text(encoding="utf-8"))
        if result.get("schema_version") != 1:
            raise ValueError("schema_version must be 1")
        case_count = result.get("case_count")
        assertion_count = result.get("assertion_count")
        selected_cases = result.get("selected_cases")
        if not isinstance(case_count, int) or case_count < 1:
            raise ValueError("case_count must be a positive integer")
        if not isinstance(assertion_count, int) or assertion_count < 1:
            raise ValueError("assertion_count must be a positive integer")
        if not isinstance(selected_cases, list) or len(selected_cases) != case_count:
            raise ValueError("selected_cases must match case_count")
        for benchmark_name in ("initial_benchmark", "revision_benchmark"):
            benchmark = result.get(benchmark_name)
            if not isinstance(benchmark, dict) or benchmark.get("total") != assertion_count:
                raise ValueError(f"{benchmark_name} total must match assertion_count")
            for field in ("candidate_passed", "baseline_passed", "assertion_delta"):
                if not isinstance(benchmark.get(field), int):
                    raise ValueError(f"{benchmark_name} {field} must be an integer")
    except (json.JSONDecodeError, ValueError) as e:
        err(f"{result_file.relative_to(ROOT)}: invalid ({e})")

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
