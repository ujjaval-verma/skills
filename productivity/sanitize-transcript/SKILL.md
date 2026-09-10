---
name: sanitize-transcript
description: Rewrite a voice-to-text meeting transcript (Zoom, Otter, Granola, dictation tools, …) with fillers, stutters and transcription artifacts removed, keeping every turn and every speaker's wording otherwise intact. Invoke only on an explicit request — "/sanitize-transcript", "clean up this transcript", "strip the ums from this", "sanitize this call transcript" — never as a side effect of summarising, quoting, or extracting action items from a meeting.
updated: 2026-09-09
---

# Sanitize transcript

Turn a raw speech-to-text transcript into a clean, complete, readable one. The **rewrite** is done by a subagent so the orchestrating session never spends its context on producing the long output; a mechanical gate then proves nothing was dropped.

## Invocation

```
/sanitize-transcript [PATH | <pasted transcript>] [--names "A=B, C=D"] [--model NAME]
```

- Input: a path to a plain-text or Markdown file (preferred), or the transcript pasted inline. Turns are `Speaker: text` lines; any label style works (`Dana Reyes:`, `Alex Kim (You):`, `[Sam]:`, `Speaker 1 (00:12):`). Subtitle formats (`.vtt`, `.srt`) are not accepted; convert them to `Speaker: text` first.
- `--names`: glossary of proper-noun corrections the operator already knows (`Acmee=Acme`). Applied verbatim; overrides the subagent's own guesses.
- `--model`: subagent model. Default `opus`; the task is long-form fidelity, so use a strong model. See `model-routing` when overriding.

## Scope

**Does:** remove fillers (`uh`, `um`, filler `like`, `you know`), stutters and false starts (`I, I, I`, `Than- thanks`, `so for so for example`), immediate word repeats, transcription garbage fragments; fix high-confidence mis-heard proper nouns and technical terms; smooth grammar only where a false start leaves a sentence unreadable.

**Does not:** summarise, shorten, reorder, merge turns, fix speaker attribution, redact PII, or add headings, timestamps, or action items. Every turn in is a turn out. Backchannels (`Mm-hmm.`, `Uh-huh.`, `Yes.`, `Okay.`) are meaningful turns and stay verbatim.

## Step 1 — Stage the input

Pasted text is written to a file **verbatim**; a path is used as-is. Output always goes to the temp dir, even when the input lives elsewhere. Define the checks once; they are reused in Steps 2 and 3.

```bash
TMP="${TMPDIR:-/tmp}"; TMP="${TMP%/}"
SLUG=<meeting-or-topic, hyphen-case>
RAW="$TMP/$SLUG-raw.txt"                     # or the path the user gave
OUT="$TMP/$SLUG-sanitized.md"
TURN_IN='^[[:alnum:]\[][^:]{0,60}(\([^)]*\))?:'   # "Label:", "Label (00:12):", "[Label]:"
TURN_OUT='^\*\*[^*]+:\*\* '
FILLER='(^|[^[:alnum:]-])([Uu][hm])([^[:alnum:]-]|$)'   # uh/um/Uh/Um; skips Uh-huh, UM
grep -oE "$TURN_IN" "$RAW" | sort | uniq -c      # eyeball: speaker labels only, no prose like "Note:"
grep -cE "$TURN_IN" "$RAW"                        # turns in — note this number
```

If the label list shows non-speaker lines, tighten `TURN_IN` to the actual labels before proceeding; an inflated count cannot be satisfied by the subagent. The orchestrating session does **not** rewrite any of the transcript itself.

## Step 2 — Dispatch one subagent

General-purpose subagent, model from `--model` (default `opus`). Keep its id for Step 3. Prompt, with `[RAW]`, `[OUT]`, `[--names]` and the three regexes filled in:

> Read the transcript at `[RAW]`. Speakers are fluent English speakers; fillers and stutters are speech-to-text artifacts. Write a sanitized but COMPLETE rewrite to `[OUT]`.
>
> 1. Keep every speaker turn, in order, attributed to the same speaker. Do not summarise, condense, merge, or reorder. Long answers stay long. Backchannel turns (`Mm-hmm.`, `Uh-huh.`, `Yes.`) stay verbatim as their own turns.
> 2. Remove only non-meaningful artifacts: standalone `uh`/`um`, filler `like`/`you know`/`kind of`, stutters and false starts, immediate word repeats, garbage fragments.
> 3. Apply this glossary verbatim: `[--names or "none"]`. Beyond it, fix a proper noun or technical term only when the intended form is near-certain from context; otherwise leave it as transcribed. A mis-heard ordinary phrase is a judgment call: fix it only if the sentence is otherwise meaningless, and list it as such.
> 4. Smooth grammar only where a false start makes a sentence unreadable. Never change numbers, claims, or substance.
> 5. Format: line 1 `# <title you derive from the content> (sanitized transcript)`; line 2 `_Participants: … Filler words, stutters and transcription artifacts removed; content otherwise unchanged._`; then one `**Speaker:** text` paragraph per turn, blank line between turns, no other line may start with `**`; finally a `## Normalisations applied` section (plain list, no bold line-starts) with every proper-noun change (`from → to`) and every judgment call (dropped fragment, ambiguous line left as-is).
> 6. Verify before reporting: `grep -cE '[TURN_IN]' [RAW]` must equal `grep -cE '[TURN_OUT]' [OUT]`, and `grep -cE '[FILLER]' [OUT] || true` must print 0. Fix and re-check until both hold. Report the path, both counts, and the normalisations list.

## Step 3 — Verify independently

Re-run the three commands from the orchestrating session. Two gates: turn parity and filler-free.

```bash
grep -cE "$TURN_IN" "$RAW"; grep -cE "$TURN_OUT" "$OUT"; grep -cE "$FILLER" "$OUT" || true
```

A gate failure is a **failure**: do not patch the file by hand and do not deliver. Locate the offending lines and send them to the same subagent (SendMessage to the id kept in Step 2):

```bash
diff <(grep -oE "$TURN_IN" "$RAW" | sed 's/ *([^)]*)//; s/[][]//g; s/:$//') \
     <(grep -oE "$TURN_OUT" "$OUT" | sed 's/^\*\*//; s/:\*\* $//')   # first divergent label = dropped/merged turn
grep -nE "$FILLER" "$OUT"                                             # surviving fillers with line numbers
```

## Step 4 — Deliver

Send `$OUT` to the user (SendUserFile or equivalent when available; otherwise state the path). In chat, give the path, the turn counts, and the normalisations list, and flag the judgment calls so the user can revert them. Transcripts are unredacted: delete the staged raw copy (never a user-supplied path), and tell the user the output sits in the temp dir until they move it.

## Common mistakes

| Mistake | Fix |
|---|---|
| Rewriting in the main session "because it's quick" | A long transcript costs tens of thousands of output tokens to rewrite; always delegate. |
| Treating `Mm-hmm.` / `Uh-huh.` turns as noise and dropping them | They carry conversational flow; the turn-parity gate catches this. |
| "Tightening" verbose answers while removing fillers | Out of scope. Fillers go; the speaker's sentences stay. |
| Silently guessing proper nouns | Every change goes in the Normalisations footer; unsure means leave it. |
| Declaring success on the subagent's word | Re-run the gates yourself before delivering. |

## Related skills

- `model-routing` — choosing the subagent model when overriding the default.
