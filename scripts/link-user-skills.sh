#!/usr/bin/env bash
set -euo pipefail

# Curated user-level skill roster.
#
# Symlinks an explicit allowlist of skills — from this repo and from a local
# checkout of mattpocock/skills — into the local harness skill directories:
#   - ~/.claude/skills  — Claude Code
#   - ~/.agents/skills  — Codex and other Agent Skills-compatible harnesses
#
# Each entry is a symlink straight into the source repo, so `git pull` in
# either repo is all that's needed to keep installed skills current.
# Re-run after changing the roster below.
#
# The roster is deliberately picky: skills excluded here are either
# repo/org-coupled (linear-sop, td-sop), superseded by an installed plugin
# (tdd, diagnosing-bugs — superpowers owns TDD and debugging), or collide
# with harness built-ins (code-review).

UJJU_REPO="$(cd "$(dirname "$0")/.." && pwd)"
MATT_REPO="${MATT_SKILLS_REPO:-$HOME/src/mattpocock/skills}"
DESTS=("$HOME/.claude/skills" "$HOME/.agents/skills")

# --- Roster: source directories, one skill folder per line ------------------

SOURCES=(
  # mattpocock/skills — productivity
  "$MATT_REPO/skills/productivity/grilling"
  "$MATT_REPO/skills/productivity/grill-me"
  "$MATT_REPO/skills/productivity/handoff"
  "$MATT_REPO/skills/productivity/writing-great-skills"
  # mattpocock/skills — engineering (wayfinder cluster + codebase-design)
  "$MATT_REPO/skills/engineering/wayfinder"
  "$MATT_REPO/skills/engineering/setup-matt-pocock-skills"
  "$MATT_REPO/skills/engineering/domain-modeling"
  "$MATT_REPO/skills/engineering/research"
  "$MATT_REPO/skills/engineering/prototype"
  "$MATT_REPO/skills/engineering/codebase-design"
  # this repo — engineering
  "$UJJU_REPO/engineering/slice-delivery"
  "$UJJU_REPO/engineering/delivery-loop"
  "$UJJU_REPO/engineering/pr-discipline"
  "$UJJU_REPO/engineering/repo-hygiene"
  "$UJJU_REPO/engineering/github-ci-triage"
)

# Previously-installed skills now off-roster; remove from each dest.
REMOVE=(
  tdd
  improve-codebase-architecture
)

# --- Validate sources before touching anything -------------------------------

for src in "${SOURCES[@]}"; do
  if [ ! -f "$src/SKILL.md" ]; then
    echo "error: $src has no SKILL.md — roster is stale or repo not checked out." >&2
    exit 1
  fi
done

# --- Link ---------------------------------------------------------------------

for DEST in "${DESTS[@]}"; do
  mkdir -p "$DEST"

  for name in "${REMOVE[@]}"; do
    target="$DEST/$name"
    if [ -L "$target" ] || [ -d "$target" ]; then
      rm -rf "$target"
      echo "removed $name ($DEST)"
    fi
  done

  for src in "${SOURCES[@]}"; do
    name="$(basename "$src")"
    target="$DEST/$name"

    # Replace stale copies (real dirs) with symlinks.
    if [ -e "$target" ] && [ ! -L "$target" ]; then
      rm -rf "$target"
    fi

    ln -sfn "$src" "$target"
    echo "linked $name -> $src ($DEST)"
  done
done
