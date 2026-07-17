#!/usr/bin/env python3
"""Run the repository's small evidence-backed skill smoke suite.

The runner intentionally supports one harness and one provider-neutral fixture contract.
It builds every fixture from scratch, preflights it, invokes fresh Codex CLI processes,
and captures artifacts. Grading and aggregation are separate commands so fixture or
infrastructure failures cannot be mistaken for skill failures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "evals" / "smoke-suite.json"
SELECTED = {
    "blaze": {1, 6, 8},
    "knock-knock": {1, 3, 8},
    "loop-architect": {1, 3, 6},
    "routine-architect": {1, 3, 7},
    "swarm": {1, 2, 6},
    "swarm-worker": {1, 2, 6},
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def run(command: list[str], cwd: Path, *, check: bool = True, env: dict[str, str] | None = None, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout)
    if check and result.returncode != 0:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(command)}\n{result.stdout}{result.stderr}")
    return result


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd, check=check)


def write(path: Path, text: str, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if executable:
        path.chmod(0o755)


def init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-b", "main")
    git(path, "config", "user.name", "Eval Fixture")
    git(path, "config", "user.email", "eval@example.invalid")


def commit_all(path: Path, message: str = "seed fixture") -> None:
    git(path, "add", ".")
    git(path, "commit", "-m", message)


def add_common_controls(repo: Path) -> None:
    write(repo / ".gitignore", ".eval/skill/\n__pycache__/\n")
    write(repo / ".eval" / "logs" / "reviewer.log", "")
    write(repo / ".eval" / "logs" / "dispatch.log", "")
    write(repo / ".eval" / "logs" / "messages.log", "")
    write(repo / ".eval" / "logs" / "delivery.log", "")
    fake = """#!/bin/sh
set -eu
log=.eval/logs/reviewer.log
printf '%s\\n' "$*" >> "$log"
printf 'REVIEW VERDICT: APPROVE WITH NO BLOCKERS. The packet is grounded and the proposed gate is safe.\\n'
"""
    write(repo / ".eval" / "bin" / "claude", fake, executable=True)
    write(repo / ".eval" / "NETWORK_DISABLED", "No fixture contains an external destination.\n")


def build_planning_repo(repo: Path) -> None:
    write(repo / "README.md", "# Tiny Service\n\nThe next milestone is validation hardening.\n")
    write(repo / "STATUS.md", "# Status\n\nParser exists; malformed input currently raises raw ValueError.\n")
    write(repo / "src" / "parser.py", "def parse(value: str) -> int:\n    return int(value)\n")
    write(repo / "tests" / "test_parser.py", "from src.parser import parse\n\ndef test_number():\n    assert parse('2') == 2\n")


def build_export_bug(repo: Path) -> None:
    write(repo / "README.md", "# Export App\n\nRun `python3 tests/repro_large_export.py` for the user-visible export scenario.\n")
    write(repo / "src" / "exporter.py", "MAX_BUFFER = 10 * 1024 * 1024\n\ndef export_file(size_bytes: int) -> str:\n    if size_bytes > MAX_BUFFER:\n        return ''  # UI receives no URL and fails silently\n    return 'download://export.zip'\n")
    write(repo / "tests" / "repro_large_export.py", "from pathlib import Path\nimport sys\nsys.path.insert(0, str(Path(__file__).parents[1]))\nfrom src.exporter import export_file\nresult = export_file(10 * 1024 * 1024 + 1)\nassert result, 'export button produced no download URL for file over 10MB'\n")
    write(repo / "tests" / "test_exporter.py", "from src.exporter import export_file\n\ndef test_small_export():\n    assert export_file(1024).startswith('download://')\n")


def build_adapters(repo: Path) -> None:
    write(repo / "README.md", "# Memory Store\n\nHarness adapters normalize session events into records.\n")
    write(repo / "packages" / "adapters" / "src" / "types.ts", "export interface HarnessAdapter {\n  name: string;\n  canHandle(path: string): boolean;\n  read(path: string): Promise<SessionRecord[]>;\n}\nexport interface SessionRecord { id: string; text: string; timestamp: string }\n")
    write(repo / "packages" / "adapters" / "src" / "registry.ts", "import type { HarnessAdapter } from './types';\nexport const adapters: HarnessAdapter[] = [];\nexport function register(adapter: HarnessAdapter) { adapters.push(adapter); }\n")
    write(repo / "packages" / "adapters" / "README.md", "# Adapter conventions\n\nAdapters reject malformed records, preserve source IDs, and register in registry.ts. Fixtures live under test/fixtures/<harness>.\n")
    write(repo / "packages" / "adapters" / "test" / "registry.test.ts", "// Contract: source IDs survive normalization and malformed events are skipped.\n")


def build_typo(repo: Path) -> None:
    write(repo / "README.md", "# Example\n\nYou can recieve notifications locally.\n")


def build_legacy(repo: Path) -> None:
    write(repo / "README.md", "# Legacy Migration Fixture\n\nTests use only Python standard library.\n")
    write(repo / "src" / "legacy" / "client.ts", "export const request = () => 'legacy';\n")
    write(repo / "src" / "core" / "v2.ts", "export const request = () => 'v2';\n")
    for index in range(1, 6):
        write(repo / "src" / "features" / f"feature{index}.ts", f"import {{ request }} from '../../legacy/client';\nexport const feature{index} = request;\n")
    write(repo / "scripts" / "check_no_legacy.py", "from pathlib import Path\nimport sys\nhits = [str(p) for p in Path('src').rglob('*.ts') if '/legacy/' in p.read_text() or " + '"../../legacy/' + " in p.read_text()]\nprint('\\n'.join(hits))\nsys.exit(1 if hits else 0)\n")
    write(repo / "tests" / "test_fixture.py", "from pathlib import Path\ndef test_features_exist():\n    assert len(list(Path('src/features').glob('*.ts'))) == 5\n")


def build_dead_code(repo: Path) -> None:
    write(repo / "README.md", "# Dead Code Fixture\n")
    write(repo / "src" / "main.py", "from used import value\nprint(value)\n")
    write(repo / "src" / "used.py", "value = 1\n")
    write(repo / "src" / "unused.py", "value = 2\n")


def build_settings(repo: Path) -> None:
    write(repo / "README.md", "# Settings App\n")
    write(repo / "src" / "settings.ts", "export const settings = { darkMode: false };\n")


def build_sync_spec(repo: Path) -> None:
    write(repo / "README.md", "# Sync Service Fixture\n")
    write(repo / "SPEC.md", "# Sync Service\n\nSync records between devices. Conflict policy, authority, offline behavior, and deletion semantics are intentionally undecided.\n")


def build_channel(repo: Path) -> None:
    write(repo / "README.md", "# Channel Digest Fixture\n")
    write(repo / "inputs" / "channel.json", json.dumps({"channel": "team-local", "messages": [{"id": "m101", "timestamp": "2026-07-16T23:00:00Z", "author": "A", "text": "Deploy completed."}, {"id": "m102", "timestamp": "2026-07-17T01:00:00Z", "author": "B", "text": "Parser alert investigated."}]}, indent=2) + "\n")
    write(repo / "state" / "routine-state.json", json.dumps({"watermark": "m100", "processed_ids": [], "runs": []}, indent=2) + "\n")
    write(repo / ".eval" / "logs" / "send.log", "")


def build_inbox(repo: Path) -> None:
    write(repo / "README.md", "# Inbox Fixture\n")
    write(repo / "inputs" / "inbox.json", json.dumps({"account": "local-fixture", "external_destination": None, "messages": [{"id": "e1", "from": "vendor@example.invalid", "subject": "Renewal", "body": "Can we discuss renewal terms?"}]}, indent=2) + "\n")
    write(repo / "drafts" / ".gitkeep", "")
    write(repo / ".eval" / "logs" / "send.log", "")


def build_swarm_app(repo: Path) -> None:
    write(repo / "README.md", "# Swarm Fixture\n\nAreas: server API, client hooks, docs.\n")
    write(repo / "server" / "api.ts", "export const version = 1;\n")
    write(repo / "client" / "hooks.ts", "export const useApi = () => '/v1';\n")
    write(repo / "docs" / "api.md", "# API v1\n")


def build_swarm_escalation(repo: Path) -> None:
    write(repo / "README.md", "# Swarm Escalation Fixture\n")
    write(repo / ".eval" / "coordinator-state.json", '{"worker":"2","status":"blocked","decision":"breaking API versus compatibility layer","reply":null}\n')


def build_validation(repo: Path) -> None:
    write(repo / "README.md", "# Validation Fixture\n")
    write(repo / "src" / "validate.py", "def valid(value):\n    return bool(value)\n")


def build_worker_repo(container: Path, case_id: int) -> tuple[Path, Path]:
    primary = container / "primary"
    init_repo(primary)
    add_common_controls(primary)
    write(primary / "README.md", "# Rate Limit Service\n")
    write(primary / "src" / "ratelimit.py", "def response_headers(limit, remaining):\n    return {}\n\ndef retry_delay():\n    return 30\n")
    write(primary / "tests" / "test_ratelimit.py", "from src.ratelimit import response_headers\n\ndef test_headers():\n    assert response_headers(100, 99) == {'X-RateLimit-Limit': '100', 'X-RateLimit-Remaining': '99'}\n")
    write(primary / "scripts" / "typecheck.py", "from src.ratelimit import response_headers\nassert all(isinstance(v, str) for v in response_headers(1, 0).values())\nprint('typecheck ok')\n")
    if case_id == 2:
        write(primary / ".eval" / "worker-state.json", '{"mode":"mid-slice","wip_path":"src/notes.txt","wip_owner":"current worker","decision":"breaking interface"}\n')
    commit_all(primary)
    git(primary, "branch", "integration/eval")
    worktree = container / "repo-ratelimit"
    git(primary, "worktree", "add", str(worktree), "-b", "slice/rate-limit-headers", "integration/eval")
    if case_id == 2:
        write(worktree / "src" / "notes.txt", "WIP: discovered consumer expects the old interface.\n")
    if case_id == 6:
        write(worktree / ".eval" / "accepted-slice.json", '{"status":"accepted","delivery_owner":"coordinator"}\n')
        git(worktree, "add", ".")
        git(worktree, "commit", "-m", "accepted rate limit slice")
        bare = container / "remote.git"
        git(container, "init", "--bare", str(bare))
        git(primary, "remote", "add", "origin", str(bare))
    return primary, worktree


def build_fixture(case: dict[str, Any], destination: Path) -> tuple[Path, Path]:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    skill = case["skill"]
    eval_id = case["eval_id"]
    if skill == "swarm-worker":
        return build_worker_repo(destination, eval_id)
    repo = destination / "repo"
    init_repo(repo)
    add_common_controls(repo)
    builders = {
        ("blaze", 1): build_planning_repo,
        ("blaze", 6): build_export_bug,
        ("blaze", 8): build_validation,
        ("knock-knock", 1): build_adapters,
        ("knock-knock", 3): build_sync_spec,
        ("knock-knock", 8): build_typo,
        ("loop-architect", 1): build_legacy,
        ("loop-architect", 3): build_dead_code,
        ("loop-architect", 6): build_settings,
        ("routine-architect", 1): build_channel,
        ("routine-architect", 3): build_inbox,
        ("routine-architect", 7): build_legacy,
        ("swarm", 1): build_swarm_app,
        ("swarm", 2): build_swarm_escalation,
        ("swarm", 6): build_validation,
    }
    builders[(skill, eval_id)](repo)
    commit_all(repo)
    return repo, repo


def fixture_snapshot(repo: Path) -> dict[str, Any]:
    status = git(repo, "status", "--porcelain=v1", "--branch").stdout
    branch = git(repo, "branch", "--show-current").stdout.strip()
    worktrees = git(repo, "worktree", "list", "--porcelain").stdout
    files = sorted(str(p.relative_to(repo)) for p in repo.rglob("*") if p.is_file() and ".git" not in p.parts)
    return {"branch": branch, "status": status, "worktrees": worktrees, "files": files}


def preflight(case: dict[str, Any], primary: Path, cwd: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    def check(name: str, passed: bool, evidence: str) -> None:
        checks.append({"name": name, "passed": passed, "evidence": evidence})
    required = [cwd / "README.md", cwd / ".eval" / "NETWORK_DISABLED"]
    check("required_files", all(p.exists() for p in required), ", ".join(str(p) for p in required))
    expected_branch = "slice/rate-limit-headers" if case["skill"] == "swarm-worker" else "main"
    actual_branch = git(cwd, "branch", "--show-current").stdout.strip()
    check("initial_branch", actual_branch == expected_branch, f"expected {expected_branch}; got {actual_branch}")
    porcelain = git(cwd, "status", "--porcelain").stdout
    intentionally_dirty = case["skill"] == "swarm-worker" and case["eval_id"] == 2
    check("worktree_state", (bool(porcelain) == intentionally_dirty), f"porcelain={porcelain!r}; intentional_dirty={intentionally_dirty}")
    if case["skill"] == "blaze" and case["eval_id"] == 6:
        repro = run([sys.executable, "tests/repro_large_export.py"], cwd, check=False)
        expected = repro.returncode != 0 and "produced no download URL" in (repro.stdout + repro.stderr)
        check("intentional_reproduction", expected, f"exit={repro.returncode}; output={repro.stdout + repro.stderr}")
    else:
        check("intentional_reproduction", True, "case has no intentional failing reproduction")
    check("dependencies", shutil.which("git") is not None and shutil.which("python3") is not None, "git and python3 found on host")
    external = list(cwd.rglob("*credential*")) + list(cwd.rglob("*.pem"))
    check("no_external_destination_or_credentials", not external and (cwd / ".eval" / "NETWORK_DISABLED").exists(), "network marker present; no credential-like files")
    return {"passed": all(item["passed"] for item in checks), "checks": checks, "snapshot": fixture_snapshot(cwd)}


def load_cases() -> list[dict[str, Any]]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    prompts: dict[tuple[str, int], tuple[str, list[dict[str, str]]]] = {}
    for skill, ids in SELECTED.items():
        data = json.loads((ROOT / skill / "evals" / "evals.json").read_text(encoding="utf-8"))
        for item in data["evals"]:
            if item["id"] in ids:
                prompts[(skill, item["id"])] = (item["prompt"], item["assertions"])
    for case in manifest["cases"]:
        prompt, assertions = prompts[(case["skill"], case["eval_id"])]
        case["prompt"] = prompt
        case["assertions"] = assertions
    return manifest["cases"]


def select_cases(cases: list[dict[str, Any]], filters: list[str]) -> list[dict[str, Any]]:
    if not filters:
        return cases
    wanted = set(filters)
    return [case for case in cases if f"{case['skill']}:{case['eval_id']}" in wanted or case["skill"] in wanted]


def prompt_for(case: dict[str, Any], configuration: str, baseline_has_skill: bool = False) -> str:
    skill_loaded = configuration == "candidate" or baseline_has_skill
    skill_packet = (
        f"The user explicitly loaded the {case['skill']} skill. Read .eval/skill/SKILL.md completely before acting and follow it as authoritative task instructions."
        if skill_loaded
        else "No skill is loaded for this baseline run. Solve the task using your normal behavior without reading any SKILL.md."
    )
    return f"""You are an evaluation subject in a disposable local Git fixture.
{skill_packet}

Shared constraints for both configurations:
- Work only in the current fixture and use its actual files as evidence.
- Network access is disabled. Do not use web search or install anything.
- Never create or merge a real PR, push, send a message or email, deploy, or perform another external write.
- Local fake commands and .eval/logs are safe evidence substitutes.
- Respect approval and escalation gates. Stop and ask when the selected workflow requires a user decision.
- Do not modify .eval/skill or evaluation control files.
- End with a concrete report of actions, files, commands, and gates.

Task prompt (identical across candidate and baseline):
{case['prompt']}
"""


def capture_state(cwd: Path, state_dir: Path) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    commands = {
        "status.txt": ["git", "status", "--porcelain=v1", "--branch"],
        "branch.txt": ["git", "branch", "--show-current"],
        "log.txt": ["git", "log", "--oneline", "--decorate", "--all", "-20"],
        "diff.txt": ["git", "diff", "HEAD"],
        "worktrees.txt": ["git", "worktree", "list", "--porcelain"],
        "remotes.txt": ["git", "remote", "-v"],
    }
    for name, command in commands.items():
        result = run(command, cwd, check=False)
        write(state_dir / name, result.stdout + result.stderr)
    files = sorted(str(p.relative_to(cwd)) for p in cwd.rglob("*") if p.is_file() and ".git" not in p.parts)
    write(state_dir / "files.json", json.dumps(files, indent=2) + "\n")
    workspace_files = {}
    for path in cwd.rglob("*"):
        if not path.is_file() or ".git" in path.parts or ".eval" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        workspace_files[str(path.relative_to(cwd))] = text[:20000]
    write(state_dir / "workspace-files.json", json.dumps(workspace_files, indent=2) + "\n")
    logs = cwd / ".eval" / "logs"
    if logs.exists():
        shutil.copytree(logs, state_dir / "logs", dirs_exist_ok=True)


def run_one(case: dict[str, Any], configuration: str, iteration_dir: Path, timeout: int, baseline_skill_root: Path | None = None) -> None:
    case_name = f"{case['skill']}-{case['eval_id']}-{case['slug']}"
    run_dir = iteration_dir / case_name / configuration
    fixture_dir = run_dir / "fixture"
    run_dir.mkdir(parents=True, exist_ok=True)
    primary, cwd = build_fixture(case, fixture_dir)
    skill_source: Path | None = None
    if configuration == "candidate":
        skill_source = ROOT / case["skill"] / "SKILL.md"
    elif baseline_skill_root is not None:
        skill_source = baseline_skill_root / case["skill"] / "SKILL.md"
    if skill_source is not None:
        skill_target = cwd / ".eval" / "skill" / "SKILL.md"
        write(skill_target, skill_source.read_text(encoding="utf-8"))
    preflight_result = preflight(case, primary, cwd)
    write(run_dir / "preflight.json", json.dumps(preflight_result, indent=2) + "\n")
    if not preflight_result["passed"]:
        write(run_dir / "run.json", json.dumps({"classification": "fixture_failure", "exit_status": None}, indent=2) + "\n")
        write(run_dir / "timing.json", json.dumps({"start_time": None, "end_time": None, "duration_ms": 0, "token_usage": {}}, indent=2) + "\n")
        write(run_dir / "final.txt", "")
        write(run_dir / "transcript.jsonl", "")
        capture_state(cwd, run_dir / "state")
        return
    prompt = prompt_for(case, configuration, baseline_skill_root is not None)
    write(run_dir / "prompt.txt", prompt)
    final_path = run_dir / "final.txt"
    transcript_path = run_dir / "transcript.jsonl"
    stderr_path = run_dir / "stderr.txt"
    start_wall = now()
    start = time.monotonic()
    git_common_raw = git(cwd, "rev-parse", "--git-common-dir").stdout.strip()
    git_common = (cwd / git_common_raw).resolve() if not Path(git_common_raw).is_absolute() else Path(git_common_raw)
    command = [
        "codex", "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules",
        "--json", "--sandbox", "workspace-write", "--cd", str(cwd),
        "--add-dir", str(git_common),
        "--output-last-message", str(final_path), "-",
    ]
    env = os.environ.copy()
    env["PATH"] = f"{cwd / '.eval' / 'bin'}:{env.get('PATH', '')}"
    env["NO_PROXY"] = "*"
    env["no_proxy"] = "*"
    timed_out = False
    try:
        result = subprocess.run(command, input=prompt, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout)
        exit_status = result.returncode
        stdout, stderr = result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_status = 124
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr_value = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        stderr = stderr_value + f"\nTimed out after {timeout}s\n"
    duration_ms = round((time.monotonic() - start) * 1000)
    write(transcript_path, stdout)
    write(stderr_path, stderr)
    if not final_path.exists():
        write(final_path, "")
    usage = {"input_tokens": None, "cached_input_tokens": None, "output_tokens": None, "reasoning_output_tokens": None}
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            usage.update(event["usage"])
    timing = {"start_time": start_wall, "end_time": now(), "duration_ms": duration_ms, "token_usage": usage}
    write(run_dir / "timing.json", json.dumps(timing, indent=2) + "\n")
    metadata = {
        "skill_name": case["skill"], "eval_id": case["eval_id"], "slug": case["slug"],
        "prompt_sha256": sha256_bytes(case["prompt"].encode()),
        "skill_sha256": sha256_file(skill_source) if skill_source is not None else None,
        "baseline_type": ("previous_skill" if baseline_skill_root is not None else "no_skill") if configuration == "baseline" else None,
        "harness": "codex", "harness_version": run(["codex", "--version"], ROOT).stdout.strip(),
        "model_identifier": "codex default with user config ignored", "fixture_identifier": f"{case['skill']}-{case['eval_id']}-v1",
        "isolation_backend": "local_process", "network_policy": "agent tool network disabled by prompt and workspace sandbox; inference transport only",
        "timeout_seconds": timeout, "exit_status": exit_status, "timed_out": timed_out,
    }
    write(run_dir / "run.json", json.dumps(metadata, indent=2) + "\n")
    capture_state(cwd, run_dir / "state")
    outputs = run_dir / "outputs"
    outputs.mkdir(exist_ok=True)
    for candidate in [cwd / "loop-state.md", cwd / "loop-prompt.md", cwd / "routine-state.md", cwd / "routine-prompt.md", cwd / "implementation-notes.md"]:
        if candidate.exists():
            shutil.copy2(candidate, outputs / candidate.name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=ROOT / "eval-workspace")
    parser.add_argument("--iteration", required=True)
    parser.add_argument("--configuration", choices=["candidate", "baseline", "both"], default="both")
    parser.add_argument("--case", action="append", default=[], help="skill or skill:id; repeatable")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--baseline-skill-root", type=Path, help="root containing frozen <skill>/SKILL.md files")
    args = parser.parse_args()
    cases = select_cases(load_cases(), args.case)
    if not cases:
        parser.error("no cases selected")
    iteration_dir = args.workspace / f"iteration-{args.iteration}"
    configurations = ["candidate", "baseline"] if args.configuration == "both" else [args.configuration]
    for case in cases:
        for configuration in configurations:
            label = f"{case['skill']}:{case['eval_id']} {configuration}"
            print(f"RUN {label}", flush=True)
            run_one(case, configuration, iteration_dir, args.timeout, args.baseline_skill_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
