#!/usr/bin/env python3
"""Freeze the current smoke-suite skill files for a revision baseline."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "evals" / "smoke-suite.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    destination = args.destination.resolve()
    cases = json.loads(MANIFEST.read_text(encoding="utf-8"))["cases"]
    skills = sorted({case["skill"] for case in cases})
    checksums = {}
    for skill in skills:
        source = ROOT / skill / "SKILL.md"
        target = destination / skill / "SKILL.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        checksums[skill] = hashlib.sha256(source.read_bytes()).hexdigest()
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "checksums.json").write_text(json.dumps(checksums, indent=2) + "\n", encoding="utf-8")
    print(f"Snapshotted {len(skills)} skills to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
