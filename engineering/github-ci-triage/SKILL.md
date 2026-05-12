---
name: github-ci-triage
description: Diagnose GitHub Actions and PR check failures with gh. Use when CI is failing, pending, cancelled, blocked, flaky, missing required checks, or when asked to inspect PR/build status and propose the smallest fix.
---

# GitHub CI Triage

Use `gh` to classify CI state before changing code. Avoid guessing from a red badge.

## Quick commands

```bash
gh pr view <pr> --json number,title,headRefName,baseRefName,mergeable,mergeStateStatus,statusCheckRollup,reviewDecision,autoMergeRequest
gh pr checks <pr> --watch=false
gh run list --branch <branch> --limit 10
gh run view <run-id> --json status,conclusion,name,event,headBranch,headSha,jobs
gh run view <run-id> --log-failed
```

For repo-wide state:

```bash
gh workflow list
gh run list --limit 20
gh api repos/:owner/:repo/branches/<base>/protection
```

## Classification

- **FAILURE**: job completed red. Fetch failed logs and find the first real failure.
- **ERROR**: infrastructure/setup problem, missing secret, bad workflow syntax, cancelled dependency.
- **CANCELLED**: usually superseded or manually cancelled. Check newer run before acting.
- **PENDING/QUEUED**: runner capacity or workflow never triggered. Check run existence.
- **BLOCKED**: required check or review gate missing. Compare branch protection required contexts to emitted checks.
- **DIRTY**: merge conflict. Use PR discipline / lockfile rules.
- **EXPECTED/SKIPPED**: confirm whether branch protection expects it anyway.

## Log-reading workflow

1. Identify the failing check name.
2. Map check → workflow run → job.
3. Fetch failed logs only first.
4. Search for first actionable error, not the final cascade:
   - test assertion before summary
   - compiler error before downstream build failure
   - dependency install error before missing binary
   - workflow syntax error before absent jobs
5. Decide fix class: code, test, config, infra, flake, docs-only skip.

## Flake discipline

Do not call something flaky from one run. Check:
- previous runs on same branch
- recent runs on base branch
- whether failure signature changes
- whether rerun passes without code changes

Use rerun sparingly, and only when the user or repo workflow authorizes external writes/actions:

```bash
gh run rerun <run-id> --failed
```

## Missing required checks

If PR is blocked but no run is pending:

1. Inspect branch protection required contexts.
2. List checks emitted by latest run on the PR.
3. Verify the workflow exists on the protected base branch.
4. If the required check producer is not on base yet, do **not** add/keep it required.

## Smallest-fix rule

Fix the first real cause with the smallest change that preserves the test’s intent.

Avoid:
- weakening assertions to make CI green
- deleting failing tests without rationale
- broad dependency upgrades for one failure
- changing branch protection to hide broken checks

## Reporting format

```markdown
CI triage:
- PR/run: 
- Failing check: 
- Classification: failure | error | blocked | pending | dirty | flake?
- First real error: 
- Proposed fix: 
- Verification: 
```
