#!/usr/bin/env bash
# Skill library lint. Run from anywhere; checks the repo containing this script.
# Fails on: name/folder drift, missing `updated:` (engineering), README index drift,
# and broken relative Markdown links in tracked *.md files.
set -euo pipefail
cd "$(dirname "$0")/.."
fail=0
err() { echo "FAIL $*"; fail=1; }

# 1. frontmatter name == folder; 2. engineering skills carry updated: YYYY-MM-DD
for f in */*/SKILL.md; do
  dir=$(basename "$(dirname "$f")")
  name=$(sed -n 's/^name:[[:space:]]*//p' "$f" | head -1)
  [ "$dir" = "$name" ] || err "name drift: $f (name=$name)"
  case "$f" in
    engineering/*)
      grep -qE '^updated:[[:space:]]*[0-9]{4}-[0-9]{2}-[0-9]{2}[[:space:]]*$' "$f" \
        || err "missing or malformed updated: in $f" ;;
  esac
done

# 3. README links every skill folder, and every README skill link resolves
for f in */*/SKILL.md; do
  rel=${f%/SKILL.md}
  grep -qF "($rel/SKILL.md)" README.md || err "README missing link to $rel"
done
while read -r p; do
  [ -e "${p%%#*}" ] || err "README links missing skill: $p"
done < <({ grep -oE '\]\((\./)?(engineering|product|productivity)/[a-z0-9-]+[^) ]*' README.md || true; } \
  | sed -E 's/^\]\((\.\/)?//' | sort -u)

# 4. relative Markdown links in tracked *.md files resolve
while IFS= read -r md; do
  [ -f "$md" ] || continue
  base=$(dirname "$md")
  while read -r link; do
    case "$link" in http://*|https://*|mailto:*|\#*) continue ;; esac
    path=${link%%#*}
    [ -n "$path" ] || continue
    case "$path" in /*) target=".$path" ;; *) target="$base/$path" ;; esac
    [ -e "$target" ] || err "broken link in $md: $link"
  done < <({ grep -oE '\]\([^) ]+' "$md" || true; } | sed 's/^](//')
done < <(git ls-files '*.md')

[ "$fail" -eq 0 ] && echo "LINT PASS" || { echo "LINT FAIL"; exit 1; }
