---
name: delivery-loop
description: Multi-slice autonomous delivery wrapper around slice-delivery. Use when an operator hands you a goal that spans multiple slices and wants them shipped in one session without per-slice approval gates. Encodes the slice queue, the T0 spec-review gate that substitutes for human-in-the-loop, the cross-slice handoff, and the explicit pause conditions that prevent the loop from running off a cliff. Triggers on "deliver multiple slices", "execute v0.X", "ship the remaining bullets", "/goal use delivery-loop".
wave: 3
updated: 2026-05-25
---

# Delivery loop

The cross-slice execution wrapper that runs `slice-delivery` in a loop without human approval between slices. Designed for sessions where the operator has already pinned the design decisions (via ADRs, invariants, and a Definition of Done) and wants the remaining mechanical work executed in one autonomous run.

This skill does **not** replace `slice-delivery` — it composes it. Each slice still runs the full slice-delivery lifecycle (brainstorm-if-needed → spec → plan → tracer bullet → incremental TDD → refactor scan → adversarial review → push). What `delivery-loop` adds is:

1. A pre-flight slice queue.
2. A T0 adversarial spec-review per slice (substitutes for human-in-the-loop at the spec→plan boundary).
3. Hard pause conditions between slices.
4. A final gate that runs the repo's Definition of Done harness.

If you only want to ship one slice, **do not invoke this skill** — invoke `slice-delivery` directly.

## Preconditions (refuse to start if any are missing)

- Repo has a Definition of Done doc and a runnable acceptance harness (`make dod` or equivalent).
- Repo has invariants, architecture, and ADRs in tracked locations.
- Repo has a `spec-review.md` doc enumerating the T0 review template.
- Repo has a `code-review.md` doc enumerating the post-code Ralph template.
- Operator has explicitly invoked this skill (do not auto-promote from `slice-delivery`).

If any precondition is missing, **stop** and tell the operator which is missing. Do not bootstrap them mid-loop — that's its own slice.

## Pre-flight (run once, before the first slice)

1. **Resolve the slice queue.** Two sources, in this order:
   - If the operator's prompt names slices explicitly (`"ship bullets 5 and 11"`, or a list), use that order verbatim.
   - Otherwise, derive from the repo's Definition of Done doc: walk current-version TODO bullets in sub-project dependency order. Bullets with no upstream blockers go first.
2. **Dump the queue to stdout BEFORE starting slice 1.** Format: numbered list with slice-id, one-line scope, source bullet(s), estimated task count. Pause for 10 seconds to give the operator a ctrl-C window if the order is wrong. State this explicitly in the dump: "Starting in 10s — ctrl-C to revise."
3. **Slice-id collision check.** For each proposed slice-id, grep `git log origin/main` for prior commits using that scope token. If any collision, **stop** and ask the operator to disambiguate. A duplicate slice-id breaks `prune-superpowers.sh` and makes the git log ambiguous.
4. **Baseline the DOD count.** Run `make dod` once, capture the pass count (e.g. `6 of 12 passing`). This is the regression floor — any subsequent run must be ≥ this count, never <.

## Per-slice loop

For each slice in the queue, in order:

### 1. Spec + plan draft

Invoke `superpowers:brainstorming` (if the slice has design ambiguity) or skip directly to spec authoring (if the slice is mechanical). Draft the spec at `docs/superpowers/specs/<YYYY-MM-DD>-<slice-id>-design.md` and the plan at `docs/superpowers/plans/<YYYY-MM-DD>-<slice-id>-plan.md`. Both follow the slice-delivery shape (one-sentence concern, task table within budget, non-scope, verification).

### 2. T0 spec-review (load-bearing pause point)

Dispatch a `feature-dev:code-reviewer` subagent with the template from `docs/engineering/spec-review.md`. The subagent reads spec + plan + invariants + ADRs + DOD doc and reports BLOCKING / NIT / DEFERRED.

Branch on the report:

- **All sections "None."** → proceed to step 3.
- **BLOCKING findings only, all mechanical** (a missing cross-reference, an inconsistent field name, a non-scope clarification, a typo in a verification criterion) → patch the spec/plan in place, record dispositions in the spec-ralph review file, **re-run T0 once**. If the second pass still has BLOCKING, fall through to the next bullet.
- **BLOCKING findings that aren't mechanical** (invariant violation, ADR contradiction, scope explosion past budget) → **stop the loop**. Surface the findings to the operator with the spec-ralph review file path. Wait for explicit resolution before continuing.
- **Any lens-B DEFERRED finding flagging a value judgment** (the spec picks a default among multiple internally-consistent options that needs human sign-off) → **stop the loop**. Surface the finding. The subagent cannot make this call; the operator can.

T0 is the human-substitute gate. The autonomy of `delivery-loop` is bounded by T0's ability to catch what a human would have caught. Trust the subagent to stop you when it should.

### 3. Tracer-bullet + incremental TDD

Run the standard `slice-delivery` lifecycle from here: tracer bullet, RED → GREEN → refactor scan per behavior, commits with `<scope>(<slice-id>): T<n> ...`. No deviation from slice-delivery's discipline.

### 4. Post-code Ralph review

Dispatch a `feature-dev:code-reviewer` subagent with the template from `docs/engineering/code-review.md`. Apply dispositions per the slice-delivery skill. Fix BLOCKING findings as separate `fix(<scope>): T<n> Ralph F<m>` commits.

### 5. Push + per-slice regression gate

Push the slice. Verify `git log origin/main..HEAD` is empty. Run `make dod` (without `CLOSEOUT=1`). Compare pass count against the baseline from pre-flight step 4.

- Pass count ≥ baseline → update the baseline to the new count, proceed to the next slice.
- Pass count < baseline → **stop the loop**. A previously-passing bullet regressed. Surface the diff in `make dod` output to the operator. Do not start the next slice.

### 6. Closeout the slice

Decide spec disposition per the rubric in `docs/engineering/code-review.md` (promote to ADR / fold into tracked doc / let it age out). Run `make prune-superpowers` (dry-run, then `APPLY=1` if the candidates look right). Move to the next slice.

## Pause conditions (hard stops, no recovery loop)

The loop **stops immediately** and surfaces to the operator when:

1. T0 spec-review returns BLOCKING that survives one mechanical retry.
2. T0 spec-review returns a lens-B DEFERRED flagging a needed value judgment.
3. Post-code Ralph review returns >1 BLOCKING finding (one BLOCKING is normal mid-slice fix territory; a cascade means something deeper is wrong).
4. `make ci` fails and the fix isn't a 5-minute mechanical patch.
5. `make dod` pass count regresses below the running baseline.
6. Pre-push hook fails for a reason other than transient network.
7. The slice-id token collides with a prior shipped slice.
8. Any task exceeds the slice scope budget (>8 tasks or >3 production Go files in `internal/`+`pkg/`).
9. Operator interrupt (ctrl-C, explicit "stop" message).

When the loop stops, the next slice has NOT started. The repo is in a clean state (the just-shipped slice is on origin/main; the in-flight slice does not exist yet). Surface the reason for the stop to the operator in plain text — file paths, log excerpts, the exact failure mode.

## Final gate (after the queue is exhausted)

1. Run `make dod CLOSEOUT=1`. This adds the no-unpushed-commits bullet.
2. Report the final state: starting pass count, ending pass count, slices shipped, slices stopped on, total commits.
3. If all DOD bullets PASS, state explicitly: `v<X> acceptance GREEN — ship`. Do not say this otherwise.

## Anti-patterns this skill prevents

- **Running v<X> as one big "ship everything" prompt.** The slice queue + per-slice T0 review keeps each spec honest.
- **Skipping the spec-review gate "because the slice is small".** Small slices accumulate lies just like large ones; the cost of T0 is bounded; skip it explicitly with reason or run it.
- **Treating "all tests pass" as "shipped".** `make ci` is the per-change gate; `make dod` is the per-version gate; the two are not interchangeable.
- **Cascading from a bad spec decision into multiple slices.** T0 catches this at the spec layer; the regression gate at step 5 catches it at the integration layer; both must hold.
- **Hiding pause conditions in the loop output.** Every stop surfaces the reason in plain text. Operators should be able to read the last 50 lines of session output and know what to do next.

## Related skills

Skills prefixed `superpowers:` are external plugin-namespaced skills (from the `superpowers` plugin set) that this skill composes when present in the host repo. They are not part of this skills library; in a repo without the superpowers plugin installed, treat each as "the repo-local equivalent if one exists, else inline the discipline manually."

- `slice-delivery` — the per-slice execution wrapper this skill composes.
- `superpowers:brainstorming` — invoked per-slice when design ambiguity exists.
- `superpowers:writing-plans` — invoked per-slice to produce the executable plan.
- `pr-discipline` — for PR-flow repos; protocol-ward bypasses PRs and ships to main, but other repos using this skill should layer pr-discipline between step 4 and step 5.
- `superpowers:verification-before-completion` — the discipline `make dod` and the regression gate enforce.

## What this skill does NOT do

- Pick the next version's goal post. That's the operator's call at the `chore(dod): bump to v<next> acceptance` boundary.
- Substitute for human design judgment on contested decisions. T0 will surface those; the operator resolves them.
- Run forever. The loop terminates when the queue is empty OR a hard stop fires. There is no retry loop on stops.
- Replace `slice-delivery`. If you are shipping one slice, use that directly.
