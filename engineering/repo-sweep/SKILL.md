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
- Nothing is ever left uncommitted at the end of a run — with one exception:
  secret or credential-looking files (`.env*`, `*.pem`, private keys, token
  files) are **never** committed or pushed; add them to `.gitignore` and call
  them out in the report instead.
- Never bypass branch protection. If origin rejects a push of `main`
  (protected branch — e.g. the skills repo requires PRs), move those commits
  intact to a pushed branch (`wip/YYYY-MM-DD`, or a PR branch via
  `gh pr create` when the work is ready), and only then set local `main` back
  to `origin/main` (`git checkout -B main origin/main` — safe because the
  commits already live on the pushed branch). Same rule when resolving a
  finished `wip/*` branch in a protected repo: land it via PR, not a direct
  merge-push. "Land via PR" means *open* the PR — never merge it yourself and
  never use `gh pr merge --admin`; merge policy (review contracts, required
  checks) belongs to humans and CI. Report the open PR URL in the summary.
- Commit messages end without AI attribution unless the repo's convention
  (recent `git log`) shows otherwise.

## Steps

0. **Recover interrupted state.** A previous run may have been killed
   mid-operation (15-minute timeout). If a rebase, merge, or cherry-pick is in
   progress (`rebase-merge`/`rebase-apply` dirs, `MERGE_HEAD`,
   `CHERRY_PICK_HEAD` under `.git/`), abort it (`git rebase --abort` /
   `git merge --abort` / `git cherry-pick --abort`) — safe because the
   commits still exist on their branches — then proceed normally.
1. **Resolve prior `wip/*` branches first.** List local and remote `wip/*`
   branches (`git for-each-ref 'refs/heads/wip/*' 'refs/remotes/origin/wip/*'`).
   For each:
   - Work now complete/ready → finish it: rebase onto `main`, shape into clean
     commits, merge into `main` (protected repo → open a PR instead; see hard
     rules), delete the branch locally and on origin once landed.
   - Already has an open PR → leave both branch and PR for the human; report.
   - Still doubtful → rebase onto `main`, push (`--force-with-lease`), keep.
   - Fully superseded by `main` → delete locally and on origin.
2. **Sync main:** if behind origin, `git pull --rebase --autostash`
   (the tree is usually still dirty at this point; `--autostash` preserves it —
   on stash-pop conflict git keeps the stash, so nothing is lost).
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
   Verification failure means the work is WIP by definition → park it, in this
   order: create `wip/YYYY-MM-DD` at the current `main` tip and push it
   **first**; only then move local `main` back to the pre-sweep tip
   (`git checkout -B main <pre-sweep-tip>`), and only if those commits were
   never pushed. Never move `main` before the commits are safe on a pushed
   branch.
6. **Push** `main` and any surviving `wip/*` branches.
7. **Report:** end with a terse summary — commits created (repo convention
   respected), work parked to wip, wip branches resolved, anything skipped
   and why.

## Related skills

- `repo-hygiene` — interactive branch/worktree cleanup with approval gates;
  repo-sweep is its autonomous, commit-focused sibling.
