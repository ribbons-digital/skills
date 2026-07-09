#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR="${SKILLS_INSTALL_DIR:-$HOME/.agents/skills}"

python3 "$ROOT/scripts/validate_skills.py"
mkdir -p "$INSTALL_DIR"

for skill_md in "$ROOT"/*/SKILL.md; do
  skill_dir="$(dirname "$skill_md")"
  skill_name="$(basename "$skill_dir")"
  rm -rf "$INSTALL_DIR/$skill_name"
  cp -R "$skill_dir" "$INSTALL_DIR/"
  echo "synced $skill_name -> $INSTALL_DIR/$skill_name"
done
