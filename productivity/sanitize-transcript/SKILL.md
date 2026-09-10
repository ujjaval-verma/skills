---
name: sanitize-transcript
description: Rewrite a voice-to-text meeting transcript (Wispr Flow, Zoom, Otter, Granola, …) with fillers, stutters and transcription artifacts removed, keeping every turn and every speaker's wording otherwise intact. Invoke only on an explicit request — "/sanitize-transcript", "clean up this transcript", "strip the ums from this", "sanitize this call transcript" — never as a side effect of summarising, quoting, or extracting action items from a meeting.
updated: 2026-09-09
---

# Sanitize transcript

Turn a raw speech-to-text transcript into a clean, complete, readable one. The rewrite is done by a **subagent** so the full transcript never has to sit in the orchestrating session's context twice.

## Invocation

```
/sanitize-transcript [PATH | <pasted transcript>] [--names "A=B, C=D"] [--model NAME]
```

- Input: a path to a `.txt`/`.md`/`.vtt` file, or the transcript pasted inline. Turns must be `Speaker: text` lines (any label style: `Alfred Lau:`, `Ujjaval Verma (You):`, `[Sri]:`).
- `--names`: glossary of proper-noun corrections the operator already knows (`Rapbook=Wrapbook`). Applied verbatim; overrides the subagent's own guesses.
- `--model`: subagent model. Default `opus`. Use a strong model — the task is long-form fidelity, not creativity.

## Scope

**Does:** remove fillers (`uh`, `um`, filler `like`, `you know`), stutters and false starts (`I, I, I`, `Than- thanks`, `so for so for example`), immediate word repeats, transcription garbage fragments; fix high-confidence mis-heard proper nouns; smooth grammar only where a false start leaves a sentence unreadable.

**Does not:** summarise, shorten, reorder, merge turns, fix speaker attribution, redact PII, or add headings, timestamps, or action items. Every turn in is a turn out. Backchannels (`Mm-hmm.`, `Yes.`, `Okay.`) are turns and stay.

## Step 1 — Stage the input

Write pasted text to a file **verbatim** (no edits, no trimming) so the subagent reads from disk:

```bash
RAW="${TMPDIR:-/tmp}/transcript-raw.txt"          # or the path the user gave
OUT="${TMPDIR:-/tmp}/<slug>-sanitized.md"          # slug: meeting/topic name, hyphen-case   # always the temp dir, even when the input was a path elsewhere
grep -cE '^[^:]{1,60}: ' "$RAW"                    # turns in — note this number
```

The orchestrating session does **not** rewrite any of the transcript itself.

## Step 2 — Dispatch one subagent

General-purpose subagent, model from `--model` (default `opus`), with this prompt, filling the bracketed fields:

> Read the transcript at `[RAW]`. Speakers are fluent English speakers; fillers and stutters are speech-to-text artifacts. Write a sanitized but COMPLETE rewrite to `[OUT]`.
>
> 1. Keep every speaker turn, in order, attributed to the same speaker. Do not summarise, condense, merge, or reorder. Long answers stay long. Backchannel turns (`Mm-hmm.`, `Yes.`) stay as their own turns.
> 2. Remove only non-meaningful artifacts: `uh`/`um`, filler `like`/`you know`/`kind of`, stutters and false starts, immediate word repeats, garbage fragments.
> 3. Apply this glossary verbatim: `[--names or "none"]`. Beyond it, fix a proper noun or technical term only when the intended form is near-certain from context; otherwise leave it as transcribed. A mis-heard ordinary phrase (`venter` → `banter`) is a judgment call: fix it only if the sentence is otherwise meaningless, and list it as such.
> 4. Smooth grammar only where a false start makes a sentence unreadable. Never change numbers, claims, or substance.
> 5. Format: line 1 `# [Title] (sanitized transcript)`; line 2 `_Participants: … Filler words, stutters and transcription artifacts removed; content otherwise unchanged._`; then one `**Speaker:** text` paragraph per turn, blank line between turns; finally a `## Normalisations applied` section listing every proper-noun change (`from → to`) and any judgment call (dropped fragment, ambiguous line left as-is).
> 6. Verify before reporting: `grep -cE '^[^:]{1,60}: ' [RAW]` must equal `grep -c '^\*\*' [OUT]`, and `grep -ciE '\b(uh|um)\b' [OUT]` must be 0. Fix and re-check until both hold. Report the path, both counts, and the normalisations list.

## Step 3 — Verify independently

Re-run the two checks from the orchestrating session. A count mismatch or surviving filler is a **failure**: send the subagent back with the specific lines, do not patch the file by hand and do not deliver.

```bash
grep -cE '^[^:]{1,60}: ' "$RAW"; grep -c '^\*\*' "$OUT"; grep -ciE '\b(uh|um)\b' "$OUT"
```

## Step 4 — Deliver

Send `$OUT` to the user (SendUserFile or equivalent when available; otherwise state the path). In chat, give the path, the turn counts, and the normalisations list, and flag any judgment calls the subagent made so the user can revert them.

## Common mistakes

| Mistake | Fix |
|---|---|
| Rewriting in the main session "because it's quick" | Long transcripts cost 50–100k tokens to rewrite; always delegate. |
| Treating `Mm-hmm.` turns as noise and dropping them | They carry conversational flow; the turn-count gate catches this. |
| "Tightening" verbose answers while removing fillers | Out of scope. Fillers go; the speaker's sentences stay. |
| Silently guessing proper nouns | Every change goes in the Normalisations footer; unsure means leave it. |
| Declaring success on the subagent's word | Re-run the counts yourself before delivering. |
