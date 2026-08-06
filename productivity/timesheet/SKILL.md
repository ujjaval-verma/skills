---
name: timesheet
description: Generate a formatted 80-column work timesheet from GitHub activity for a date range, optionally scoped to a repo or org. Invoke only on an explicit request — "/timesheet", "generate a timesheet", "what did I work on last week" — never as a side effect of summarising activity, reviewing commits, or answering questions about a repo's history.
updated: 2026-08-05
---

# Timesheet

Generate a formatted 80-column timesheet from GitHub activity.

## Invocation

```
/timesheet START END [OWNER/REPO | ORG]
```

- `START`, `END`: dates in `YYYY-MM-DD` format (inclusive)
- Optional: a repo (`owner/repo`) or org name to scope results

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

## Step 3 — Synthesize per-day summaries

Group all commits and PRs by date. For each date with activity, write a 1–3 sentence plain-English summary of the work (no bullet points, no SHA references). Combine related work into one narrative.

**Hours estimation** (use your judgment):
- Light day (1–2 small commits): 2.0–3.0 h
- Moderate day (3–5 commits or 1 PR): 4.0–5.0 h
- Heavy day (6+ commits or multiple PRs): 6.0–8.0 h

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
