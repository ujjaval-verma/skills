---
name: timesheet
description: Generate a work timesheet from GitHub activity for a date range — as an 80-column table or an HTML page — optionally scoped to a repo or org. Counts roadmapping effort (issues, milestones, review comments, planning documents) by default; a flag gives a code-only sheet. Invoke only on an explicit request — "/timesheet", "generate a timesheet", "what did I work on last week" — never as a side effect of summarising activity, reviewing commits, or answering questions about a repo's history.
updated: 2026-08-27
---

# Timesheet

Generate a per-day work timesheet from GitHub activity.

## Invocation

```
/timesheet START END [OWNER/REPO | ORG] [--skip-non-code-effort[=true|false]] [--html] [--docs PATH...]
```

- `START`, `END`: dates in `YYYY-MM-DD` format, inclusive, **in the user's local timezone**. Natural-language dates in the request ("Aug 15–23") are normalised to this form first; a year-less range takes the current year.
- Optional scope: a repo (`owner/repo`) or org name. It must come before any `--` flag.
- `--skip-non-code-effort` (default **false**; bare flag means `true`): when false, roadmapping and planning effort is counted alongside code — see Step 2b. Set true for a code-only sheet.
- `--html`: write the sheet as an HTML page in the OS temp directory (Step 4b) instead of printing the 80-column table. A request that says "html", "web page" or "file" implies this flag.
- `--docs PATH...`: extra local git checkouts (or subdirectories) holding planning documents for the engagement — memos, roadmaps, decision records, timesheets. Their commit history in the window is counted as non-code effort. Ignored when `--skip-non-code-effort` is true.

**Engagement name** (used in the title and filename): the client name if the user gave one, otherwise the repo name; for an org scope, the org name.

## Step 1 — Gather identity and bounds

```bash
set -o pipefail   # every fetch below is `gh | jq`; without this a failed gh call yields an empty section and a clean exit
GH_USER=$(gh api user --jq '.login')
START=<from invocation>; END=<from invocation>     # YYYY-MM-DD, substitute the requested dates

# GitHub compares against UTC instants and treats a bare date as 00:00Z — a bare END drops the
# last local day entirely. Convert the local-day bounds to UTC once (macOS and GNU date):
to_utc(){ local s; s=$(date -j -f "%Y-%m-%d %H:%M:%S" "$1" +%s 2>/dev/null) || s=$(date -d "$1" +%s)
          date -u -r "$s" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d "@$s" +%Y-%m-%dT%H:%M:%SZ; }
START_UTC=$(to_utc "$START 00:00:00"); END_UTC=$(to_utc "$END 23:59:59")   # e.g. 2026-08-15T04:00:00Z 2026-08-24T03:59:59Z
```

Run Steps 1–2b and 4b in a **single** shell call (shell state does not persist between calls), or re-declare the variables in each.

## Step 2 — Fetch code activity

**Specific repo:**
```bash
gh search commits --author "$GH_USER" --author-date "$START_UTC..$END_UTC" \
  --repo OWNER/REPO --json sha,commit,repository --limit 1000

gh search prs --author "$GH_USER" --repo OWNER/REPO \
  --created "$START_UTC..$END_UTC" --json title,createdAt,state --limit 1000
```

**Org-scoped:** replace `--repo OWNER/REPO` with `--owner ORG` and add `repository` to the PR `--json` list.

**No scope (all repos):** drop the `--repo`/`--owner` flag.

If a local checkout is at hand, prefer it for the commit list — it is complete (search indexing lags) and its `%ai` timestamps carry the local offset, which decides the day a late-night commit belongs to:

```bash
git -C PATH log --all --since "$START" --until "$END 23:59:59" --format='%ai %s'
```

`--until "$END 23:59:59"` is portable; never write `END+1day` — git parses it silently as garbage.

**Sanity check:** if `gh search` returns 0 commits but `git log` returns some, the UTC bounds are wrong (re-check `to_utc` output) — stop and fix it before continuing.

## Step 2b — Fetch non-code effort (unless `--skip-non-code-effort`)

Roadmapping, planning and review work rarely shows up as commits. Gather, for the same window, only the user's own activity. `gh --jq` accepts a bare expression only (no `--arg`), so pipe JSON to `jq` instead:

```bash
REPO=OWNER/REPO
W='select(.created_at >= $s and .created_at <= $e)'

# Issues the user filed (--limit truncates silently to the newest N: if the count equals the limit, raise it)
gh issue list --repo "$REPO" --state all --limit 200 --author "$GH_USER" \
  --json number,title,createdAt,closedAt,milestone,labels \
  | jq -r --arg s "$START_UTC" --arg e "$END_UTC" \
      '.[] | select(.createdAt >= $s and .createdAt <= $e) | "\(.createdAt[:10]) #\(.number) \(.title)"'

# Issues the user closed (search has no closed-by qualifier; the timeline event carries the actor)
gh issue list --repo "$REPO" --state closed --limit 200 --search "closed:$START_UTC..$END_UTC" \
  --json number --jq '.[].number' | while read -r n; do
  gh api "repos/$REPO/issues/$n/timeline" --paginate \
    | jq -r --arg u "$GH_USER" --arg n "$n" --arg s "$START_UTC" --arg e "$END_UTC" \
        '.[] | select(.event=="closed" and .actor.login==$u and .created_at >= $s and .created_at <= $e) | "\(.created_at[:10]) closed #\($n)"'
done

# Issue/PR conversation comments and PR review comments (two different endpoints).
# `since` filters on updated_at, so the window is re-applied on created_at.
for ep in issues/comments pulls/comments; do
  gh api "repos/$REPO/$ep?since=$START_UTC" --paginate \
    | jq -r --arg u "$GH_USER" --arg s "$START_UTC" --arg e "$END_UTC" \
        ".[] | select(.user.login==\$u) | $W | \"\(.created_at[:10]) \(.html_url)\""
done

# Milestones
gh api "repos/$REPO/milestones?state=all" --paginate \
  | jq -r --arg s "$START_UTC" --arg e "$END_UTC" \
      ".[] | $W | \"\(.created_at[:10]) \(.title) open=\(.open_issues) closed=\(.closed_issues)\""

# Planning documents in --docs checkouts
git -C PATH log --all --since "$START" --until "$END 23:59:59" --format='%ai %s' --name-only
```

The dates printed by these commands are UTC (`[:10]` of an ISO instant); convert to local time before assigning a day — an evening item in UTC-4 prints as the next day. Also read the repo's own `docs/` for dated documents — decision records, roadmaps, blocker/risk registers, research notes — whose *content* dates fall in the window; a document committed on the last day often records work done across the week.

**Strictly separate evidence from inference.** A day supported only by content dates (not by a commit, issue, comment or review on that day) may be listed, but the method note (Step 4) must name those days.

## Step 3 — Synthesize per-day summaries

Group everything by local date. For each date with activity, write one 2–5 sentence plain-English narrative (no bullet points, no SHAs, no file paths). Issue numbers are fine in parentheses — they are the client's own tracker IDs. Combine related work into one story per day.

**Register — write for the person paying the invoice, not for an engineer.** Describe only what the evidence shows; translate jargon, never multiply artifacts.

| Evidence | Say | Don't say |
|---|---|---|
| Milestone created + N issues filed into it | "established the delivery milestone and decomposed it into N scoped work items" | "created milestone, opened N issues" |
| Issue triage, labels, closures | "prioritised / re-sequenced / consolidated the backlog" | "labelled issues, closed duplicates" |
| PR review comments | "reviewed the X change and returned N findings" | "left comments on PR #12" |
| An ADR on topic X | "recorded the architecture decision on X" | "wrote ADR-0004" |
| A roadmap document | "authored the N-week roadmap" | "added roadmap-8-week.md" |
| A blocker or risk register | "set up the blockers register" | "added blockers.md" |
| Research notes on X | "discovery research into X" | "wrote research/03-…md" |
| Scaffold, CI, hooks | "stood up the repository and its quality gate" | "added pre-commit hook, justfile" |
| Code commits | the capability delivered, in product terms | file names, function names |

Technical nouns the client already uses (product names, standards, model names) are fine; internal file paths, tool flags and jargon are not.

**Hours estimation** (use your judgment):
- Light day (1–2 small commits, or a handful of issue edits): 2.0–3.0 h
- Moderate day (3–5 commits, 1 PR, or ~10 issues scoped / a planning memo): 4.0–6.0 h
- Heavy day (6+ commits, multiple PRs, a milestone stood up with its issues, or several planning documents): 6.0–9.0 h

A single commit that lands thousands of lines of documentation is heavy, not light — size by content, not by commit count. Days with zero activity are omitted entirely. Never invent activity to fill a gap; report the gap instead.

## Step 4 — Output

Always finish with a **method note** stating: the flag values used; the sources consulted; the timezone used for day boundaries; the count of code commits in the window; which days (if any) are inferred from content dates rather than dated activity; what in-window activity was excluded (other engagements) and what near-window activity was left out (e.g. a milestone filed the day after `END`); and that hours are judgment estimates.

### 4a — Markdown table (default)

Column widths (between pipes): date=12, hours=7, summary=57. Summary text wraps at **55 characters** of content.

```
| Date       | Hours | Work Summary                                            |
| :--------- | :---- | :------------------------------------------------------ |
| 2026-03-01 | 4.0   | First 55 chars of summary here, wrapped if              |
|            |       | longer than 55 chars continues on the next line         |
| Total      | 21.0  |                                                         |
```

- Break at word boundaries ≤55 chars; never mid-word.
- Continuation rows: date cell = 12 spaces, hours cell = 7 spaces.
- Last row is `Total` with the sum of hours; summary cell is empty (spaces to fill).
- Verify final table width = 80 chars before outputting. Put the method note below the table as a short paragraph.

### 4b — HTML page (`--html`)

1. In the same shell call as Step 1 (or with `START`/`END` re-declared), create the file from the template — `<skill-dir>` is the directory holding this `SKILL.md`:
   ```bash
   OUT="$(mktemp -d)/timesheet-<engagement>-$START-to-$END.html"   # e.g. timesheet-toro-ai-2026-08-15-to-2026-08-23.html
   cp <skill-dir>/template.html "$OUT"; echo "$OUT"
   ```
2. Fill **all 15** `{{…}}` placeholders — `TITLE`, `ENGAGEMENT`, `PERIOD` ("15 – 23 August 2026 (inclusive)"), `PERSON` (`gh api user --jq .name`), `REPOS`, `SCOPE` (one sentence), `ROWS` (one `<tr>` per day, ascending; delete the example comment above it), `TOTAL`, `SKIP_NON_CODE` (`true`/`false`), `SKIP_NON_CODE_MEANING`, `SOURCES`, `COMMIT_COUNT`, `EVIDENCE_NOTE` (inferred days, timezone), `EXCLUSIONS`, `EMPTY_DAYS`. Escape `&`, `<`, `>` in text (no attributes are interpolated, so quotes need no escaping); use `&ldquo;…&rdquo;` for quotes and `&nbsp;` between a number and its unit.
3. Do not add scripts, external stylesheets or fonts — the page must render offline from a file URL.
4. Before delivering: `grep -o '{{' "$OUT" | wc -l` must print `0`.
5. Print the absolute path in the reply, and if a file-delivery tool is available, send the file as well.

Client-visible rows from previous sheets are the style reference; keep the same voice from period to period so the sheets read as one series.
