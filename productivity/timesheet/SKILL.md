---
name: timesheet
description: Generate a formatted 80-column work timesheet from GitHub activity for a date range, optionally scoped to a repo or org. Invoke only on an explicit request — "/timesheet", "generate a timesheet", "what did I work on last week" — never as a side effect of summarising activity, reviewing commits, or answering questions about a repo's history.
updated: 2026-08-23
---

# Timesheet

Generate a formatted 80-column timesheet from GitHub activity.

## Invocation

```
/timesheet START END [OWNER/REPO | ORG] [--include-roadmapping]
```

- `START`, `END`: dates in `YYYY-MM-DD` format (inclusive)
- Optional: a repo (`owner/repo`) or org name to scope results

## Flags

| Flag | Default | Effect |
| ---- | ------- | ------ |
| `skip-non-code-effort` | `true` | Only commits and PRs are counted (the original behaviour). Pass `--include-roadmapping` (sets it to `false`) to also count roadmapping effort: GitHub issues created/triaged, milestone work, substantive issue comments, and planning/roadmap document commits in a docs repo (e.g. `docs-uv`). A prompt that asks for roadmapping/planning effort in prose also sets it to `false`. |

Defaults MUST NOT change: with no flag and no explicit ask, behave exactly as
before (commits + PRs only). Every generated timesheet MUST explicitly state
the flag values used for that run (see Steps 4–5).

## Step 1 — Gather identity

```bash
GH_USER=$(gh api user --jq '.login')
```

## Step 2 — Fetch activity

**Specific repo:**
```bash
gh search commits --author "$GH_USER" --author-date "START..END" \
  --repo OWNER/REPO --json sha,commit,repository --limit 100

gh search prs --author "$GH_USER" --repo OWNER/REPO \
  --created "START..END" --json title,createdAt,state --limit 100
```

**Org-scoped:**
```bash
gh search commits --author "$GH_USER" --author-date "START..END" \
  --owner ORG --json sha,commit,repository --limit 100

gh search prs --author "$GH_USER" --owner ORG \
  --created "START..END" --json title,createdAt,repository --limit 100
```

**No scope (all repos):**
```bash
gh search commits --author "$GH_USER" --author-date "START..END" \
  --json sha,commit,repository --limit 100

gh search prs --author "$GH_USER" --created "START..END" \
  --json title,createdAt,repository --limit 100
```

## Step 2b — Fetch roadmapping activity (only when `skip-non-code-effort: false`)

Skip this step entirely under the default flag value. When roadmapping is
included, additionally gather for the same window:

```bash
# Issues created (with milestone, to show triage structure)
gh issue list -R OWNER/REPO --author "$GH_USER" --state all \
  --search "created:START..END" --limit 100 \
  --json number,title,createdAt,milestone

# Issues triaged/updated in the window (milestone moves, re-scoping)
gh issue list -R OWNER/REPO --state all \
  --search "updated:START..END" --limit 100 --json number,title,updatedAt

# Substantive issue comments by the user
gh api "search/issues?q=repo:OWNER/REPO+commenter:$GH_USER+updated:START..END&per_page=100" \
  --jq '.items[].number' | while read n; do
  gh api "repos/OWNER/REPO/issues/$n/comments?per_page=100" \
    --jq ".[]|select(.user.login==\"$GH_USER\")|\"\(.created_at[:10]) #$n (\(.body|length) chars)\""
done

# Milestones created or updated in the window
gh api "repos/OWNER/REPO/milestones?state=all" \
  --jq '.[]|"\(.created_at[:10])/\(.updated_at[:10]) \(.title) (open \(.open_issues), closed \(.closed_issues))"'
```

**Planning-document repos:** if a docs/roadmap repo exists (for this practice:
`~/src/ujjaval-verma/docs-uv`, scoped to the engagement's subdirectory), pull
its commits for the window too:

```bash
git -C ~/src/ujjaval-verma/docs-uv log --since=START --until=END+1 \
  --format='%ad %h %s' --date=short --stat -- <engagement-dir>/
```

Filter to the engagement at hand — exclude unrelated clients and internal
practice tooling. Note that issue-comment `updated` search matches the issue's
update date, so filter comment dates to the window yourself.

## Step 3 — Synthesize per-day summaries

Group all commits and PRs — plus, when roadmapping is included, issues filed,
milestone/triage work, comments, and planning-doc commits — by date. For each date with activity, write a 1–3 sentence plain-English summary of the work (no bullet points, no SHA references). Combine related work into one narrative.

**Hours estimation** (use your judgment):
- Light day (1–2 small commits): 2.0–3.0 h
- Moderate day (3–5 commits or 1 PR): 4.0–5.0 h
- Heavy day (6+ commits or multiple PRs): 6.0–8.0 h

When roadmapping is included, weigh it the same way: a batch of well-scoped
issues (~30–45 min each with scope notes), a planning deck or memo written or
substantially revised (2–3 h), milestone triage (~1 h per session).

**Framing roadmapping work:** describe it in project-management and product-
roadmapping terms that show the judgement behind the artifacts — never in
clerical terms that read as inventing work. Avoid "filed N issues",
"created tickets", "wrote comments". Instead, name the product activity the
artifacts evidence and group items by theme (trust, conversion, revenue
integrity, resilience, polish):

- "filed nine issues" → "decomposed the workstreams into nine scoped,
  sequenced work items with acceptance notes"
- "filed issues from a walkthrough" → "conducted a product and security
  walkthrough and translated the findings into scoped milestone work items"
- "moved issues into the milestone" → "consolidated / re-prioritised existing
  backlog items against the new plan"
- "created a milestone" → "established X as the organising delivery milestone"
- "wrote a deck/memo" → "authored the readiness assessment / re-sequenced
  delivery via the queue memo"

The verbs are audit, assess, decompose, scope, sequence, prioritise, triage,
consolidate, establish, author, re-sequence — always anchored to the real
GitHub/doc artifacts gathered in Step 2b, never embellished beyond them.

Days with zero activity are omitted entirely.

## Step 4 — Format the table

Column widths (between pipes): date=12, hours=7, summary=57.
Summary text wraps at **55 characters** of content.

```
| Date       | Hours | Work Summary                                            |
| :--------- | :---- | :------------------------------------------------------ |
| 2026-03-01 | 4.0   | First 55 chars of summary here, wrapped if              |
|            |       | longer than 55 chars continues on the next line         |
| Total      | 21.0  |                                                         |
```

**Wrapping rules:**
- Break at word boundaries ≤55 chars; never mid-word.
- Continuation rows: date cell = 12 spaces, hours cell = 7 spaces.
- Last row is `Total` with sum of hours; summary cell is empty (spaces to fill).

**Cell padding template:**
```
| YYYY-MM-DD | H.H   | <55 chars padded to 55 with trailing spaces>            |
|            |       | <continuation line>                                     |
```

Verify final table width = 80 chars before outputting.

Immediately after the table, state the flag values used for the run, e.g.:

```
Flags used: skip-non-code-effort: true (commits and PRs only).
```

or, when roadmapping was included, name the extra sources (issues, milestones,
comments, docs-repo commits) alongside `skip-non-code-effort: false`.

## Step 5 — Emit the HTML timesheet

Always also write a copy-paste-ready HTML version to the OS temp directory
(`$TMPDIR` or `/tmp`), named `timesheet-<scope>-<START>-<END>.html`, and send
it to the user with SendUserFile (`display: render`). Requirements:

- Self-contained (no external assets); pin `data-theme="light"` on `<html>`
  and set an explicit light background — temp HTML files render on a light
  ground.
- Header block: period (inclusive), person, repo/org scope, and a one-line
  scope statement.
- The same per-day table (date / hours / summary) with a visually distinct
  Total row; clean borders so the table pastes intact into email or docs.
- A method note repeating the flag values used, the sources consulted, and
  that hours are judgment estimates with zero-activity days omitted.
