---
name: api-cost-estimate
description: Estimate what local Claude Code token usage would have cost on pay-as-you-go API pricing, per model, for a date window (default last 7 days). Invoke only on an explicit request — "/api-cost-estimate", "what would this week have cost on the API", "API-equivalent cost of my usage" — never as a side effect of discussing usage, rate limits, or model choice.
updated: 2026-08-25
---

# API cost estimate

Two box-drawn tables — per-model token usage and per-model estimated cost — computed from local Claude Code transcripts and Anthropic's published first-party API rates. Answers "what would my subscription usage have cost on a pure API plan?"

## Invocation

```
/api-cost-estimate [START] [END]
```

- No args: last 7 days (UTC midnight, 7 days ago → now).
- `START` (`YYYY-MM-DD`): window starts at 00:00 UTC that day → now.
- `START END`: inclusive; `END` runs to 23:59:59 UTC.

## Step 1 — Run the script

```bash
python3 <skill-dir>/scripts/estimate.py [START] [END]
```

`<skill-dir>` is the directory holding this `SKILL.md`. The script needs only the standard library and reads `~/.claude/projects/**/*.jsonl` (assistant turns only, deduped by message id + request id — retries and streamed partials are not double-counted).

## Step 2 — Check the pricing table

Rates are hard-coded in `DEFAULT_PRICES` inside the script (USD per 1M tokens; cache write = 1.25× input for the 5-minute TTL, cache read = 0.1× input). Before reporting:

- If the `claude-api` skill is available, compare its model/pricing table against `DEFAULT_PRICES`. On a mismatch, or a model the script reports as *unpriced*, pass a corrected table via `--prices prices.json` (`{"model-prefix": ["Display name", input, output]}`) and note the correction in the reply. Update `DEFAULT_PRICES` in the same PR if the change is durable.
- Never guess a rate from memory.

## Step 3 — Report

Paste both tables verbatim inside a single fenced code block, then add at most three lines of context:

- the 1-hour-cache-TTL upper bound the script prints (writes billed at 2× instead of 1.25×);
- the biggest cost driver (usually cache reads, not output);
- scope caveat: only sessions whose transcripts are on this machine are counted.

Don't editorialise about whether the subscription is "worth it" unless asked.
