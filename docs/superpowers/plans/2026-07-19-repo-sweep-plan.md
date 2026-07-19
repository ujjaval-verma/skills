# repo-sweep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the scheduled commit janitor from the approved spec — a `repo-sweep` skill (judgment), an orchestration script (deterministic pre-flight), and a launchd agent (schedule) that sweep uncommitted work in three active repos into well-shaped, pushed commits ~3x/day.

**Architecture:** launchd fires `~/src/ujjaval-verma/repo-sweep.sh` at 12:00 / 17:00 / 21:30. The script does zero-token git pre-flight per repo (lock, fetch, needs-sweep test, active-editing guard, ff-only cheap path) and only invokes headless `claude -p --dangerously-skip-permissions "/repo-sweep"` when judgment is needed. All judgment lives in the committed skill `engineering/repo-sweep/SKILL.md`, installed as a user skill via `scripts/link-user-skills.sh`. Idempotency state lives in git itself — no state file.

**Tech Stack:** bash, git, launchd (macOS), Claude Code headless mode, AgentSkill Markdown.

**Spec (source of truth):** `/Users/ujju/src/ujjaval-verma/skills/docs/superpowers/specs/2026-07-19-repo-sweep-design.md`. Do not redesign; every content requirement below cites its spec section.

## Global Constraints

- **Committed vs uncommitted:** Tasks 1–2 are committed to the skills repo (`/Users/ujju/src/ujjaval-verma/skills`). Tasks 3–5 produce artifacts that live **outside any git repo** and are **never committed**: `~/src/ujjaval-verma/repo-sweep.sh` (spec §2: "uncommitted; that dir is not a repo") and `~/Library/LaunchAgents/com.ujjaval.repo-sweep.plist`.
- **Repo conventions (CLAUDE.md / CONTRIBUTING.md):** Conventional Commits scoped by skill (`feat(repo-sweep): …`); `main` is branch-protected (PR + linear history, no direct pushes) — do committed work on a branch; README **Skills** table *and* **Triggers** table must be updated in the same PR as the new skill; frontmatter must carry `name` (matches folder), trigger-oriented `description`, `updated: 2026-07-19`. Do **not** assign `wave:` (no documented cohort). Non-trivial PR → adversarial (Ralph) review trail required before merge.
- **Skill placement:** `engineering/` category, alongside `repo-hygiene` and `pr-discipline` (spec §3). Deliberate decision: repo-sweep is a standalone automated entry point (invoked by the scheduled job), **not** part of the slice-delivery→pr-discipline composition stack — do not touch the composition diagrams in CLAUDE.md/README.
- **Hard safety rules (spec §3, verbatim):** never force-push `main`; never delete uncommitted work (no `checkout --`, `clean`, or `reset --hard` on user changes); never rewrite pushed `main` history (`wip/*` rebase is the sole exception, force-with-lease permitted for `wip/*` only); commit messages end without AI attribution unless the repo's convention shows otherwise. Per the spec's 2026-07-19 erratum: never bypass branch protection — when origin rejects a `main` push (skills repo), land via a pushed branch/PR instead.
- **Schedule/paths (spec §1–2, verbatim):** fire times 12:00, 17:00, 21:30 daily; lock at `~/src/ujjaval-verma/.repo-sweep/lock` (stale >2h reclaimed); logs in `~/src/ujjaval-verma/.repo-sweep/logs/` (`launchd.log` + `YYYY-MM-DD-HHMM-<repo>.log`, 30-day retention); per-repo Claude timeout 15 minutes; repo list hardcoded: `~/src/ujjaval-verma/skills`, `~/src/ujjaval-verma/fight-club`, `~/src/ujjaval-verma/docs-uv`; active-editing guard 15 minutes; load via `launchctl bootstrap gui/$UID <plist>` (not `launchctl load`).
- **No automated test suite exists in this repo** — each task's "test" is its stated verification command with expected output. `--dry-run` and observed manual runs (spec §Testing/rollout) are the acceptance tests for Tasks 3–5.

---

### Task 1: `engineering/repo-sweep/SKILL.md` + README index rows (committed)

**Files:**
- Create: `/Users/ujju/src/ujjaval-verma/skills/engineering/repo-sweep/SKILL.md`
- Modify: `/Users/ujju/src/ujjaval-verma/skills/README.md` (Skills table ~line 53, after the `repo-hygiene` row; Triggers table ~line 83, after the `repo-hygiene` row)

**Interfaces:**
- Consumes: nothing (first task).
- Produces: skill folder `engineering/repo-sweep` with `SKILL.md` whose frontmatter `name:` is exactly `repo-sweep` — Task 2's roster entry and Task 5's `/repo-sweep` slash invocation both resolve against this name.

- [ ] **Step 1: Create a working branch**

```bash
cd /Users/ujju/src/ujjaval-verma/skills
git checkout -b repo-sweep-skill
```

- [ ] **Step 2: Write `SKILL.md`**

Content requirements traced to spec §3 (ordered steps 1–7) and §Decisions (WIP handling). The skill is repo-agnostic in body — it operates on the cwd; the hardcoded repo list lives only in the script (Task 3), satisfying the "no user paths in skills" rule. Write exactly:

```markdown
---
name: repo-sweep
description: Autonomous sweep of the current repo (the cwd) — resolve prior wip/* branches, sync main, group uncommitted work into coherent commits, triage ready work to main vs doubtful work to a wip/YYYY-MM-DD branch, verify, and push. Use when invoked headless as /repo-sweep by the scheduled sweep job, or when asked to sweep uncommitted work into commits and push.
updated: 2026-07-19
---

# Repo Sweep

Scheduled commit janitor. Runs headless inside one repo (the cwd), autonomously:
fix everything you can, commit and push without asking. Idempotent — state lives
in git itself; a run against an already-swept repo is a no-op. Execute the steps
in order.

## Hard rules

- Never force-push `main`. Never rewrite history that exists on origin —
  `wip/*` rebase is the sole exception (`--force-with-lease` permitted for
  `wip/*` branches only; they are unshared by convention).
- Never delete uncommitted work: no `checkout --`, `git clean`, or
  `reset --hard` on user changes. Work is only ever added to commits/branches,
  never destroyed — every intermediate state must be safe to abandon.
- Nothing is ever left uncommitted at the end of a run.
- Never bypass branch protection. If origin rejects a push of `main`
  (protected branch — e.g. the skills repo requires PRs), move those commits
  intact to a pushed branch (`wip/YYYY-MM-DD`, or a PR branch via
  `gh pr create` when the work is ready), and only then set local `main` back
  to `origin/main` (`git checkout -B main origin/main` — safe because the
  commits already live on the pushed branch). Same rule when resolving a
  finished `wip/*` branch in a protected repo: land it via PR, not a direct
  merge-push.
- Commit messages end without AI attribution unless the repo's convention
  (recent `git log`) shows otherwise.

## Steps

1. **Resolve prior `wip/*` branches first.** List local and remote `wip/*`
   branches (`git for-each-ref 'refs/heads/wip/*' 'refs/remotes/origin/wip/*'`).
   For each:
   - Work now complete/ready → finish it: rebase onto `main`, shape into clean
     commits, merge into `main`, delete the branch locally and on origin.
   - Still doubtful → rebase onto `main`, push (`--force-with-lease`), keep.
   - Fully superseded by `main` → delete locally and on origin.
2. **Sync main:** if behind origin, `git pull --rebase`.
3. **Sweep the working tree:** group uncommitted + untracked changes into
   coherent logical commits. Detect the repo's commit convention from recent
   `git log` and match it. Tool/cache artifacts (e.g. `.tokensave/`) are added
   to `.gitignore` rather than committed.
4. **Triage ready vs WIP:** ready → commits on `main`. Incomplete, broken, or
   doubtful → committed to `wip/YYYY-MM-DD` (today's date; created from `main`
   if absent — if today's branch already exists from an earlier run and
   survived step 1, commit onto it instead of re-creating), pushed; `main` is
   left untouched by that work.
5. **Verify before pushing main:** if the repo defines a gate, run it —
   `make -f .ujju-ct/Makefile check` when `.ujju-ct` exists, else `make check`
   when a Makefile defines that target; docs-only repos have no gate.
   Verification failure means the work is WIP by definition → move it to the
   wip branch instead (branch from the pre-sweep `main` tip, cherry-pick or
   reset `main` back only if those commits were never pushed).
6. **Push** `main` and any surviving `wip/*` branches.
7. **Report:** end with a terse summary — commits created (repo convention
   respected), work parked to wip, wip branches resolved, anything skipped
   and why.

## Related skills

- `repo-hygiene` — interactive branch/worktree cleanup with approval gates;
  repo-sweep is its autonomous, commit-focused sibling.
```

- [ ] **Step 3: Add the README Skills table row**

In `/Users/ujju/src/ujjaval-verma/skills/README.md`, insert after the `engineering/repo-hygiene` row (line 53) to keep alphabetical order:

```markdown
| [`engineering/repo-sweep`](engineering/repo-sweep/SKILL.md) | Autonomous scheduled sweep of one repo: resolve `wip/*` branches, group uncommitted work into coherent commits, triage ready→`main` vs doubtful→`wip/YYYY-MM-DD`, verify, push. |
```

- [ ] **Step 4: Add the README Triggers table row**

Insert after the `repo-hygiene` Triggers row (line 83):

```markdown
| *(headless — invoked as `/repo-sweep` by the scheduled sweep job)*, *"sweep uncommitted work into commits"* | [`repo-sweep`](engineering/repo-sweep/SKILL.md) |
```

- [ ] **Step 5: Verify frontmatter/folder/index consistency**

Run:
```bash
cd /Users/ujju/src/ujjaval-verma/skills
grep -c "name: repo-sweep" engineering/repo-sweep/SKILL.md
grep -c "engineering/repo-sweep" README.md
```
Expected: `1` and `2` (one Skills row + one Triggers row).

- [ ] **Step 6: Commit**

```bash
cd /Users/ujju/src/ujjaval-verma/skills
git add engineering/repo-sweep/SKILL.md README.md
git commit -m "feat(repo-sweep): add autonomous scheduled sweep skill"
```

---

### Task 2: Roster entry in `scripts/link-user-skills.sh` + install (committed)

**Files:**
- Modify: `/Users/ujju/src/ujjaval-verma/skills/scripts/link-user-skills.sh:45` (SOURCES array, "this repo — engineering" block)

**Interfaces:**
- Consumes: `engineering/repo-sweep/SKILL.md` from Task 1 (the script validates `$src/SKILL.md` exists and exits 1 otherwise — Task 1 must be complete first).
- Produces: symlinks `~/.claude/skills/repo-sweep` and `~/.agents/skills/repo-sweep` → the repo folder. Task 5's headless `claude -p ... "/repo-sweep"` resolves the skill through these symlinks. Note: because entries are symlinks into the source repo, later edits to the skill need no re-run — but **this roster addition does require one re-run** to create the links (spec §3).

- [ ] **Step 1: Add the roster line**

In the `SOURCES` array, after the `repo-hygiene` line (line 44), insert:

```bash
  "$UJJU_REPO/engineering/repo-sweep"
```

- [ ] **Step 2: Re-run the script to install the symlinks**

Run:
```bash
bash /Users/ujju/src/ujjaval-verma/skills/scripts/link-user-skills.sh
```
Expected output includes: `linked repo-sweep -> /Users/ujju/src/ujjaval-verma/skills/engineering/repo-sweep` for **both** dests (`~/.claude/skills` and `~/.agents/skills`), exit 0.

- [ ] **Step 3: Verify the symlinks resolve**

```bash
readlink ~/.claude/skills/repo-sweep && test -f ~/.claude/skills/repo-sweep/SKILL.md && echo OK
readlink ~/.agents/skills/repo-sweep && test -f ~/.agents/skills/repo-sweep/SKILL.md && echo OK
```
Expected: each prints the repo path then `OK`.

- [ ] **Step 4: Commit, push, open PR**

```bash
cd /Users/ujju/src/ujjaval-verma/skills
git add scripts/link-user-skills.sh
git commit -m "feat(repo-sweep): add repo-sweep to the user-level skill roster"
git push -u origin HEAD
gh pr create --fill
```
Then run the repo's adversarial (Ralph) review contract on the PR before merge (dispatch an independent reviewer subagent, post findings as a PR comment, disposition every finding — see CLAUDE.md § Adversarial review). Merge before starting Task 5 (the headless run reads the skill through the symlink, which points at the checkout — so strictly the branch being checked out locally suffices for testing, but merge before enabling the schedule).

---

### Task 3: Sweep script `~/src/ujjaval-verma/repo-sweep.sh` (UNCOMMITTED — outside any repo)

**Files:**
- Create: `/Users/ujju/src/ujjaval-verma/repo-sweep.sh` (`~/src/ujjaval-verma` is not a git repo; do not `git add` this file anywhere — spec §2)

**Interfaces:**
- Consumes: the installed `repo-sweep` user skill from Task 2 (invoked as the `/repo-sweep` slash command).
- Produces: an executable script taking optional `--dry-run`; exit 0 = all repos OK/skipped, non-zero = at least one repo failed (spec §2.6). Task 4's plist executes it via `/bin/bash /Users/ujju/src/ujjaval-verma/repo-sweep.sh`. Creates/uses `~/src/ujjaval-verma/.repo-sweep/{lock,logs/}`.

- [ ] **Step 1: Write the script**

Content requirements traced to spec §2 items 1–8 (lock, hardcoded repo list, pure-git pre-flight, cheap ff-only path, 15-min active-editing guard, 15-min-timeout Claude invocation, failure isolation, `--dry-run`, 30-day log retention) and §Error handling. macOS has no `timeout(1)`, hence the portable `run_with_timeout`; launchd provides a minimal `PATH`, hence the export. Write exactly:

```bash
#!/usr/bin/env bash
# repo-sweep.sh — deterministic orchestration for the scheduled commit janitor.
# All judgment lives in the repo-sweep skill; this script is pure pre-flight.
# UNCOMMITTED by design: ~/src/ujjaval-verma is not a git repo (see spec
# skills/docs/superpowers/specs/2026-07-19-repo-sweep-design.md).
set -uo pipefail   # no -e: failure isolation is per-repo (spec §2.6)

SWEEP_HOME="$HOME/src/ujjaval-verma/.repo-sweep"
LOCK_DIR="$SWEEP_HOME/lock"
LOG_DIR="$SWEEP_HOME/logs"
REPOS=(
  "$HOME/src/ujjaval-verma/skills"
  "$HOME/src/ujjaval-verma/fight-club"
  "$HOME/src/ujjaval-verma/docs-uv"
)
CLAUDE_TIMEOUT_SECS=$((15 * 60))   # spec §2.5
STALE_LOCK_SECS=$((2 * 60 * 60))   # spec §2.1
ACTIVE_EDIT_SECS=$((15 * 60))      # spec §2.4

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

# launchd provides a minimal PATH; make claude/git/gh resolvable.
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

mkdir -p "$LOG_DIR"
log() { printf '%s %s\n' "$(date '+%F %T')" "$*"; }

# --- Lock (spec §2.1): mkdir-based; held → exit 0; stale >2h reclaimed -------
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  lock_mtime=$(stat -f %m "$LOCK_DIR" 2>/dev/null || echo 0)
  if [ $(( $(date +%s) - lock_mtime )) -gt "$STALE_LOCK_SECS" ]; then
    log "reclaiming stale lock (>2h old)"
    rm -rf "$LOCK_DIR"
    mkdir "$LOCK_DIR" 2>/dev/null || { log "lock race lost; exiting"; exit 0; }
  else
    log "lock held; another run in progress; exiting"
    exit 0
  fi
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT

# --- Log retention (spec §2.8): prune logs older than 30 days ----------------
find "$LOG_DIR" -name '*.log' -type f -mtime +30 -delete 2>/dev/null

# --- Portable 15-min timeout (macOS lacks timeout(1)) ------------------------
run_with_timeout() { # <secs> <cmd...>; returns cmd's exit code, or 143 on kill
  local secs=$1; shift
  "$@" &
  local cmd_pid=$!
  ( sleep "$secs"; kill -TERM "$cmd_pid" 2>/dev/null
    sleep 15; kill -KILL "$cmd_pid" 2>/dev/null ) &   # escalate if TERM ignored
  local killer_pid=$!
  wait "$cmd_pid"; local rc=$?
  kill "$killer_pid" 2>/dev/null; wait "$killer_pid" 2>/dev/null
  return "$rc"
}

sweep_repo() {
  local repo=$1 name; name=$(basename "$repo")
  local repo_log="$LOG_DIR/$(date '+%Y-%m-%d-%H%M')-$name.log"

  # Fetch (spec §2.3): failure → log, skip; offline is a normal state.
  if ! git -C "$repo" fetch origin --prune --quiet 2>>"$repo_log"; then
    log "$name: fetch failed (offline?); skipping"
    return 0
  fi

  # Needs-sweep test (spec §2.3) — the idempotency core; state is git itself.
  local dirty="" unpushed="" behind="" wip=""
  [ -n "$(git -C "$repo" status --porcelain)" ] && dirty=1
  if git -C "$repo" rev-parse --abbrev-ref '@{u}' >/dev/null 2>&1; then
    [ -n "$(git -C "$repo" rev-list '@{u}..HEAD' 2>/dev/null)" ] && unpushed=1
    [ -n "$(git -C "$repo" rev-list 'HEAD..@{u}' 2>/dev/null)" ] && behind=1
  fi
  git -C "$repo" for-each-ref 'refs/heads/wip/*' 'refs/remotes/origin/wip/*' \
    | grep -q . && wip=1

  if [ -z "$dirty$unpushed$behind$wip" ]; then
    log "$name: nothing to sweep; skip"
    return 0
  fi

  # Cheap path (spec §2.3): only-behind → ff-only pull, no Claude.
  if [ -n "$behind" ] && [ -z "$dirty$unpushed$wip" ]; then
    if [ "$DRY_RUN" = 1 ]; then
      log "$name: DRY-RUN decision: ff-only pull (behind only)"
      return 0
    fi
    if git -C "$repo" pull --ff-only --quiet >>"$repo_log" 2>&1; then
      log "$name: behind only; ff-only pull done"
      return 0
    fi
    log "$name: ff-only pull failed (diverged); falling through to claude"
  fi

  # Active-editing guard (spec §2.4): any dirty file touched <15 min → skip.
  # Deleted/renamed-away files have no mtime and don't trigger the guard.
  local now line f mtime
  now=$(date +%s)
  while IFS= read -r line; do
    f="${line:3}"
    case "$f" in *' -> '*) f="${f##* -> }" ;; esac   # renames: check new path
    [ -e "$repo/$f" ] || continue
    mtime=$(stat -f %m "$repo/$f" 2>/dev/null || echo 0)
    if [ $(( now - mtime )) -lt "$ACTIVE_EDIT_SECS" ]; then
      log "$name: '$f' modified <15m ago (user mid-edit?); skipping this run"
      return 0
    fi
  done < <(git -C "$repo" status --porcelain)

  if [ "$DRY_RUN" = 1 ]; then
    log "$name: DRY-RUN decision: invoke claude" \
        "(dirty=${dirty:-0} unpushed=${unpushed:-0} behind=${behind:-0} wip=${wip:-0})"
    return 0
  fi

  # Invoke (spec §2.5): headless skill run, 15-min timeout, per-repo log.
  log "$name: invoking claude /repo-sweep -> $repo_log"
  if ( cd "$repo" && run_with_timeout "$CLAUDE_TIMEOUT_SECS" \
        claude -p --dangerously-skip-permissions "/repo-sweep" ) \
        >>"$repo_log" 2>&1; then
    log "$name: sweep OK"
    return 0
  fi
  log "$name: sweep FAILED (see $repo_log)"
  return 1
}

# --- Main loop (spec §2.6): failure isolation; non-zero exit if any failed ---
FAILED=0
for repo in "${REPOS[@]}"; do
  if [ ! -d "$repo/.git" ]; then
    log "$(basename "$repo"): not a git repo at $repo; skipping"
    continue
  fi
  sweep_repo "$repo" || FAILED=1
done
exit "$FAILED"
```

- [ ] **Step 2: Make executable and syntax-check**

```bash
chmod +x /Users/ujju/src/ujjaval-verma/repo-sweep.sh
bash -n /Users/ujju/src/ujjaval-verma/repo-sweep.sh && echo SYNTAX-OK
command -v shellcheck >/dev/null && shellcheck /Users/ujju/src/ujjaval-verma/repo-sweep.sh || true
```
Expected: `SYNTAX-OK`; shellcheck (if installed) reports no errors (info/style notes acceptable).

- [ ] **Step 3: Smoke the lock and dry-run plumbing**

```bash
/Users/ujju/src/ujjaval-verma/repo-sweep.sh --dry-run
echo "exit=$?"
ls /Users/ujju/src/ujjaval-verma/.repo-sweep/logs >/dev/null && echo LOGDIR-OK
test ! -d /Users/ujju/src/ujjaval-verma/.repo-sweep/lock && echo LOCK-RELEASED
```
Expected: one `DRY-RUN decision:` / `nothing to sweep` / `fetch failed` line per repo, `exit=0`, `LOGDIR-OK`, `LOCK-RELEASED`. No `claude` process is spawned (dry-run invokes nothing — spec §2.7). Do not commit this file anywhere.

---

### Task 4: launchd agent `~/Library/LaunchAgents/com.ujjaval.repo-sweep.plist` (outside any repo)

**Files:**
- Create: `/Users/ujju/Library/LaunchAgents/com.ujjaval.repo-sweep.plist`

**Interfaces:**
- Consumes: `/Users/ujju/src/ujjaval-verma/repo-sweep.sh` from Task 3.
- Produces: launchd job labeled `com.ujjaval.repo-sweep`; Task 5 bootstraps and verifies it. Not loaded yet in this task.

- [ ] **Step 1: Write the plist**

Content requirements traced to spec §1: `StartCalendarInterval` at 12:00, 17:00, 21:30 (launchd's default behavior already runs a missed calendar interval once on wake — no extra key needed); stdout/stderr to `~/src/ujjaval-verma/.repo-sweep/logs/launchd.log`. launchd plists cannot use `~`, so paths are absolute. Write exactly:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.ujjaval.repo-sweep</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>/Users/ujju/src/ujjaval-verma/repo-sweep.sh</string>
  </array>
  <key>StartCalendarInterval</key>
  <array>
    <dict>
      <key>Hour</key><integer>12</integer>
      <key>Minute</key><integer>0</integer>
    </dict>
    <dict>
      <key>Hour</key><integer>17</integer>
      <key>Minute</key><integer>0</integer>
    </dict>
    <dict>
      <key>Hour</key><integer>21</integer>
      <key>Minute</key><integer>30</integer>
    </dict>
  </array>
  <key>StandardOutPath</key>
  <string>/Users/ujju/src/ujjaval-verma/.repo-sweep/logs/launchd.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/ujju/src/ujjaval-verma/.repo-sweep/logs/launchd.log</string>
</dict>
</plist>
```

- [ ] **Step 2: Lint the plist**

```bash
plutil -lint /Users/ujju/Library/LaunchAgents/com.ujjaval.repo-sweep.plist
```
Expected: `.../com.ujjaval.repo-sweep.plist: OK`. Do not bootstrap yet — that is Task 5, after the observed manual runs.

---

### Task 5: Rollout — dry-run, observed manual runs, bootstrap, verify (spec §Testing/rollout)

**Files:**
- No new files. Operates on the artifacts from Tasks 1–4.

**Interfaces:**
- Consumes: merged skill + roster symlinks (Tasks 1–2), `repo-sweep.sh` (Task 3), plist (Task 4).
- Produces: a loaded launchd job with a verified next fire time; the system is live.

- [ ] **Step 1: Dry-run against known repo states (spec rollout step 1)**

First record the ground truth, then compare against the script's decisions:
```bash
for r in ~/src/ujjaval-verma/skills ~/src/ujjaval-verma/fight-club ~/src/ujjaval-verma/docs-uv; do
  echo "== $r"
  git -C "$r" status --porcelain | head -5
  git -C "$r" rev-list '@{u}..HEAD' 2>/dev/null | head -3
  git -C "$r" for-each-ref 'refs/heads/wip/*' 'refs/remotes/origin/wip/*'
done
/Users/ujju/src/ujjaval-verma/repo-sweep.sh --dry-run
```
Expected: for every repo, the DRY-RUN decision line matches the observed git state (dirty → "invoke claude"; clean+current → "nothing to sweep"; behind-only → "ff-only pull"). If any decision contradicts the git state, stop and fix Task 3 before proceeding.

- [ ] **Step 2: One observed manual real run per repo (spec rollout step 2)**

For each of the three repos, by hand, watching the output:
```bash
cd ~/src/ujjaval-verma/skills    && claude -p --dangerously-skip-permissions "/repo-sweep"
cd ~/src/ujjaval-verma/fight-club && claude -p --dangerously-skip-permissions "/repo-sweep"
cd ~/src/ujjaval-verma/docs-uv    && claude -p --dangerously-skip-permissions "/repo-sweep"
```
Expected per repo, checked against the skill contract: terse end-of-run report; no uncommitted work left (`git status --porcelain` empty); ready work on `main` and pushed; doubtful work on a pushed `wip/YYYY-MM-DD` branch; commit messages match the repo's convention (Conventional Commits in skills; plain imperative in fight-club and docs-uv); no force-push of `main` in the reflog/remote. If a run misbehaves, fix the SKILL.md wording (Task 1) — bump `updated:` — and re-observe before scheduling.

- [ ] **Step 3: Verify idempotency (spec §Problem: "already-swept repo is a no-op")**

Immediately re-run the orchestrator for real:
```bash
/Users/ujju/src/ujjaval-verma/repo-sweep.sh; echo "exit=$?"
```
Expected: every repo logs `nothing to sweep; skip` (or ff-only pull), `exit=0`, and **no** Claude invocation occurs (no new `YYYY-MM-DD-HHMM-<repo>.log` with claude output). Exception: if a `wip/*` branch survived Step 2, that repo **will** invoke Claude by design (spec §2.3 treats any `wip/*` as needs-sweep); the git-level no-op there is a run ending "kept wip branch, no changes".

- [ ] **Step 4: Bootstrap the launchd agent (spec §1: modern syntax, not `launchctl load`)**

```bash
mkdir -p /Users/ujju/src/ujjaval-verma/.repo-sweep/logs   # launchd does NOT create parent dirs for StandardOutPath; missing dir = silently dropped output
launchctl bootstrap gui/$UID /Users/ujju/Library/LaunchAgents/com.ujjaval.repo-sweep.plist
```
Expected: silent exit 0. (If re-installing after an edit: `launchctl bootout gui/$UID/com.ujjaval.repo-sweep` first.)

- [ ] **Step 5: Verify the job and its next fire (spec rollout step 3)**

```bash
launchctl print gui/$UID/com.ujjaval.repo-sweep | head -40
```
Expected: `state = waiting`, the three `com.ujjaval.repo-sweep` calendar intervals visible (12:00, 17:00, 21:30), stdout/stderr paths pointing at `.repo-sweep/logs/launchd.log`. Optionally force one supervised firing without waiting for the clock:
```bash
launchctl kickstart gui/$UID/com.ujjaval.repo-sweep
sleep 5 && tail -20 /Users/ujju/src/ujjaval-verma/.repo-sweep/logs/launchd.log
```
Expected: fresh timestamped per-repo decision lines in `launchd.log`.

---

## Out of scope (v1, per spec)

Failure notifications, `--remote-control` observation mode, repos beyond the three listed (adding one later = one line in the script's `REPOS` array).
