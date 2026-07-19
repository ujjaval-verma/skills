# repo-sweep — scheduled commit janitor for active repos

**Date:** 2026-07-19
**Status:** Approved

## Problem

Three actively-edited repos (`~/src/ujjaval-verma/skills`, `~/src/ujjaval-verma/fight-club`,
`~/src/ujjaval-verma/docs-uv`) accumulate uncommitted work through the day. The goal is a
scheduled job (~3x/day) that consolidates uncommitted changes into well-shaped commits and
ensures they reach the remote in good shape — autonomously, and idempotently (a run against
an already-swept repo is a no-op).

## Decisions (from brainstorming)

- **Job purpose:** review new commits + repo hygiene, but primarily: sweep uncommitted work
  into coherent commits and push.
- **Autonomy:** fix everything it can; commit and push autonomously.
- **WIP handling:** ready work → clean commits on `main`, pushed. Doubtful/incomplete work →
  committed to a `wip/YYYY-MM-DD` branch and pushed. Subsequent runs MUST actively look for
  and resolve prior `wip/*` branches before sweeping new work.
- **Mechanism:** launchd (not cron) → deterministic shell script → per-repo headless
  `claude -p --dangerously-skip-permissions "/repo-sweep"` invocation driven by a user skill.

## Components

### 1. launchd agent — `~/Library/LaunchAgents/com.ujjaval.repo-sweep.plist`

- `StartCalendarInterval`: 12:00, 17:00, 21:30 daily.
- launchd runs a missed interval on wake if the machine was asleep.
- `StandardOutPath`/`StandardErrorPath` → `~/src/ujjaval-verma/.repo-sweep/logs/launchd.log`.
- Loaded via `launchctl bootstrap gui/$UID <plist>` (modern syntax; not `launchctl load`).

### 2. Sweep script — `~/src/ujjaval-verma/repo-sweep.sh` (uncommitted; that dir is not a repo)

Deterministic orchestration only — no judgment. Per run:

1. **Lock:** `mkdir`-based lock (e.g. `~/src/ujjaval-verma/.repo-sweep/lock`); if held, exit 0
   immediately. Lock removed on exit via trap. A stale lock older than 2 hours is reclaimed.
2. **Repo list:** hardcoded array of the three repo paths.
3. **Per-repo pre-flight, pure git (zero tokens):**
   - `git fetch origin --prune` (failure → log, skip repo: offline is a normal state).
   - Needs-sweep test — any of: dirty tree or untracked files (`git status --porcelain`
     non-empty), unpushed commits (`git rev-list @{u}..HEAD` non-empty), behind origin,
     any local or remote `wip/*` branch.
   - If none: skip repo. **This is the idempotency core — state lives in git itself; no
     separate state file.**
   - Cheap-path exception: if the *only* trigger is "behind origin" (clean tree, nothing
     unpushed, no `wip/*`), the script runs `git pull --ff-only` itself and skips the
     Claude invocation. If the ff-only pull fails (diverged), invoke Claude normally.
4. **Active-editing guard:** if any file reported by `git status --porcelain` has mtime
   within the last 15 minutes, skip the repo this run (user likely mid-edit; next run
   picks it up). Deleted files (no mtime) don't trigger the guard.
5. **Invoke:** `cd <repo> && claude -p --dangerously-skip-permissions "/repo-sweep"` with a
   per-repo timeout of 15 minutes; append stdout/stderr to
   `~/src/ujjaval-verma/.repo-sweep/logs/YYYY-MM-DD-HHMM-<repo>.log`.
6. **Failure isolation:** a failing repo logs and the loop continues to the next repo.
   Script exit code is non-zero if any repo failed (visible in launchd log).
7. **Flags:** `--dry-run` prints per-repo pre-flight decisions and invokes nothing.
8. **Log retention:** prune log files older than 30 days at the start of each run.

### 3. `repo-sweep` skill — `skills/engineering/repo-sweep/SKILL.md`

Committed to the skills repo (engineering category, alongside repo-hygiene and
pr-discipline), added to the roster in `scripts/link-user-skills.sh`, and installed by
re-running that script (symlinks into `~/.claude/skills` and `~/.agents/skills`).

All judgment lives here. Ordered steps, executed inside one repo (the cwd):

1. **Resolve prior `wip/*` branches first.** For each local or remote `wip/*` branch:
   - Work now complete/ready → finish it: rebase onto `main`, shape into clean commits,
     merge into `main`, delete the branch locally and on origin.
   - Still doubtful → rebase onto `main` (branch is unshared-by-convention; rebase OK),
     push (force-with-lease permitted for `wip/*` only), keep.
   - Fully superseded by `main` → delete locally and on origin.
2. **Sync main:** if behind origin, pull with rebase. Never force-push `main`; never
   rewrite history that exists on origin (`wip/*` rebase is the sole exception).
3. **Sweep the working tree:** group uncommitted + untracked changes into coherent logical
   commits. Detect the repo's commit convention from recent `git log` (conventional
   commits in skills; plain imperative sentences in fight-club and docs-uv). Tool/cache
   artifacts (e.g. `.tokensave/`) are added to `.gitignore` rather than committed.
4. **Triage ready vs WIP:** ready → commits on `main`. Incomplete, broken, or doubtful →
   committed to `wip/YYYY-MM-DD` (created from `main`), pushed; `main` is left untouched
   by that work. Nothing is ever left uncommitted at the end of a run.
5. **Verify before pushing main:** if the repo defines a gate, run it —
   `make -f .ujju-ct/Makefile check` when `.ujju-ct` exists, else `make check` when a
   Makefile defines it; docs-only repos have no gate. Verification failure means the work
   is WIP by definition → park it on the wip branch instead.
6. **Push** `main` and any surviving `wip/*` branches.
7. **Report:** end with a terse summary — commits created (repo convention respected),
   work parked to wip, wip branches resolved, anything skipped and why.

Hard rules: never force-push `main`; never delete uncommitted work (no `checkout --`,
`clean`, or `reset --hard` on user changes); never rewrite pushed `main` history; commit
messages end without AI attribution unless the repo's convention shows otherwise.

## Error handling

- Offline / fetch failure: skip repo, log, non-fatal.
- Claude invocation timeout or non-zero exit: logged; repo left in whatever git state the
  run reached — by design every intermediate state is safe (work is only ever added to
  commits/branches, never destroyed), and the next run resumes from git state.
- Overlap: lockfile guarantees single concurrent run.

## Testing / rollout

1. `repo-sweep.sh --dry-run` — verify pre-flight decisions against known repo states.
2. One manual real run per repo (`claude -p ... "/repo-sweep"` by hand), observed.
3. Load the launchd plist; verify next scheduled fire via `launchctl print`.

## Out of scope (v1)

- Notifications on failure (bolt-on later via launchd or the report log).
- `--remote-control` observation mode.
- Repos beyond the three listed (adding one = one line in the script's array).
