---
name: delivery-loop
description: Multi-slice autonomous delivery wrapper around slice-delivery — operator-invoked loop that ships a pre-flight slice queue against a supplied Definition of Done via per-slice subagents.
disable-model-invocation: true
wave: 3
updated: 2026-07-15
---

# Delivery loop

The cross-slice execution wrapper that runs `slice-delivery` in a loop without human approval between slices. Designed for sessions where the operator has already pinned the design decisions (via ADRs, invariants, and a Definition of Done) and wants the remaining mechanical work executed in one autonomous run.

This skill does **not** replace `slice-delivery` — it composes it. Each slice still runs the full slice-delivery lifecycle (brainstorm-if-needed → spec → plan → tracer bullet → incremental TDD → refactor scan → adversarial review → push). What `delivery-loop` adds is:

1. A pre-flight slice queue.
2. A T0 adversarial spec-review per slice (substitutes for human-in-the-loop at the spec→plan boundary).
3. **Per-slice subagent dispatch** — the orchestrating session stays lean; slices execute in fresh contexts.
4. Hard pause conditions between slices.
5. A final gate that runs the Definition of Done harness.

If you only want to ship one slice, **do not invoke this skill** — invoke `slice-delivery` directly.

## The DOD is an input, not an assumption

The operator **must supply a Definition of Done** when invoking this skill, in one of two forms:

- **Inline** — acceptance bullets stated directly in the prompt.
- **By reference** — a path or URL to a DOD artifact (a `DEFINITION-OF-DONE.md`, a tracked doc, a tracker milestone) plus, ideally, the command that checks it (`make dod`, a test tag, a script — "the DOD harness").

If no DOD is supplied and none is discoverable at a conventional location the operator confirms, **refuse to start**. A delivery loop without a DOD has no termination condition and no regression floor. Do not synthesize one mid-loop — proposing a DOD is its own (human-gated) task.

If the DOD has bullets but no runnable harness, the loop still works: the per-slice regression gate degrades from "harness pass count" to "explicit bullet-by-bullet check recorded in the slice's PR/commit". Say which mode you're in during pre-flight.

## Preconditions (refuse to start if any are missing)

- A Definition of Done supplied as input (see above).
- Repo has invariants / architecture notes / ADRs in tracked locations (or the operator explicitly waives this with "no invariants exist yet").
- A spec-review template (repo-local `spec-review.md` or equivalent). If none exists, use the T0 lens set inline in this skill's step 2.
- Operator has explicitly invoked this skill (do not auto-promote from `slice-delivery`).

If a precondition is missing, **stop** and tell the operator which one. Do not bootstrap them mid-loop — that's its own slice.

## Pre-flight (run once, before the first slice)

1. **Resolve the slice queue.** Two sources, in this order:
   - If the operator's prompt names slices explicitly (`"ship bullets 5 and 11"`, or a list), use that order verbatim.
   - Otherwise, derive from the DOD input: walk unmet bullets in dependency order. Bullets with no upstream blockers go first.
2. **Dump the queue to stdout BEFORE starting slice 1.** Format: numbered list with slice-id, one-line scope, source bullet(s), estimated task count. Pause to give the operator an interrupt window if the order is wrong. State this explicitly in the dump: "Starting shortly — interrupt to revise."
3. **Slice-id collision check.** For each proposed slice-id, grep `git log origin/<default-branch>` for prior commits using that scope token. If any collision, **stop** and ask the operator to disambiguate — a duplicate slice-id makes the git log ambiguous.
4. **Baseline the DOD.** Run the DOD harness once and capture the pass count (e.g. `6 of 12 passing`); with no harness, record which bullets are currently met. This is the regression floor — any subsequent check must be ≥ this, never <.

## Subagent-driven delivery

Each slice executes in a **dispatched subagent** with a fresh context, not in the orchestrating session. This is the default, not an optimization: an N-slice loop run inline accumulates N slices of diffs, test output, and review traffic until the orchestrator can no longer hold its own gates.

- **The orchestrator holds only**: the DOD input, the queue, the in-flight slice's spec + plan (which it drafts in step 1), per-slice gate verdicts, the regression baseline, and one-paragraph summaries of shipped slices. It reads subagent reports; it does not read slice diffs. If spec drafting itself needs heavy exploration (a long `superpowers:brainstorming` run), delegate that to a subagent too and keep only the resulting spec.
- **Each slice subagent receives**: the slice's spec + plan, the DOD input, pointers to invariants/ADRs, the branch/worktree to work in, and the instruction to run the full `slice-delivery` lifecycle (compose `superpowers:subagent-driven-development` where installed).
- **Each slice subagent returns**: slice-id, what shipped (PR/commits), verification evidence, Ralph review dispositions, and anything that smells like a pause condition. The orchestrator — not the subagent — decides whether to continue the loop.
- **Sequential by default.** Run one slice subagent at a time, in queue order. Dispatch slices in parallel only when they are provably independent (no shared files, no DOD-bullet overlap) and each gets its own worktree (`superpowers:using-git-worktrees`); the regression gate then runs after the wave, not per slice.
- The T0 spec-review and post-code Ralph review are **separate subagents** from the slice implementer — the reviewer must not share context (or authorship) with what it reviews.

For very long queues, the orchestrator turn itself can be re-entered on a cadence with the `/loop` skill — each firing processes the next slice(s) and re-checks the pause conditions. Never let `/loop` bypass a pause condition: a hard stop ends the loop, cadence or not.

## Per-slice loop

For each slice in the queue, in order:

### 1. Spec + plan draft

Invoke `superpowers:brainstorming` (if the slice has design ambiguity) or skip directly to spec authoring (if the slice is mechanical). Draft the spec and plan wherever the repo keeps transient planning artifacts (per `slice-delivery`'s durable-vs-transient rule). Both follow the slice-delivery shape (one-sentence concern, task table within budget, non-scope, verification).

### 2. T0 spec-review (load-bearing pause point)

Dispatch an adversarial code-reviewer subagent per `slice-delivery`'s start-lane T0 (the repo's spec-review template, or its fallback lens set A/B/C). The subagent reads spec + plan + invariants + ADRs + DOD and reports BLOCKING / NIT / DEFERRED.

Branch on the report:

- **All sections "None."** → proceed to step 3.
- **BLOCKING findings only, all mechanical** (a missing cross-reference, an inconsistent field name, a non-scope clarification, a typo in a verification criterion) → patch the spec/plan in place, record dispositions, **re-run T0 once**. If the second pass still has BLOCKING, fall through to the next bullet.
- **BLOCKING findings that aren't mechanical** (invariant violation, ADR contradiction, scope explosion past budget) → **stop the loop**. Surface the findings to the operator with the review artifact path. Wait for explicit resolution before continuing.
- **Any lens-B DEFERRED finding flagging a value judgment** (the spec picks a default among multiple internally-consistent options that needs human sign-off) → **stop the loop**. Surface the finding. The subagent cannot make this call; the operator can.

T0 is the human-substitute gate. The autonomy of `delivery-loop` is bounded by T0's ability to catch what a human would have caught. Trust the subagent to stop you when it should.

### 3. Dispatch the slice subagent

Hand the approved spec + plan to a fresh implementation subagent per **Subagent-driven delivery** above. It runs the standard `slice-delivery` lifecycle end to end — no deviation from its discipline, including commit format.

### 4. Post-code Ralph review

Dispatch a separate adversarial code-reviewer subagent with the repo's code-review template (or `slice-delivery`'s Ralph contract, absent one) against the slice's diff. Apply dispositions per the slice-delivery skill. BLOCKING findings go back to the implementation subagent (or a fresh one) as `fix(<scope>): T<n> Ralph F<m>` commits.

### 5. Push + per-slice regression gate

Push the slice (via `pr-discipline` in PR-flow repos). Verify nothing unpushed remains. Run the DOD check and compare against the baseline from pre-flight step 4.

- Result ≥ baseline → update the baseline, proceed to the next slice.
- Result < baseline → **stop the loop**. A previously-met bullet regressed. Surface the DOD diff to the operator. Do not start the next slice.

### 6. Closeout the slice

Fold the slice's transient spec/plan artifacts per the repo's disposition rubric (promote to ADR / fold into a tracked doc / let them age out). Run the repo's closeout/hygiene script if it has one (else `repo-hygiene` for worktree/branch cleanup). Record the one-paragraph slice summary in the orchestrator. Move to the next slice.

## Pause conditions (hard stops, no recovery loop)

The loop **stops immediately** and surfaces to the operator when:

1. T0 spec-review returns BLOCKING that survives one mechanical retry.
2. T0 spec-review returns a lens-B DEFERRED flagging a needed value judgment.
3. Post-code Ralph review returns >1 BLOCKING finding (one BLOCKING is normal mid-slice fix territory; a cascade means something deeper is wrong).
4. The repo's CI gate fails and the fix isn't a 5-minute mechanical patch.
5. The DOD check regresses below the running baseline.
6. A pre-push/pre-commit hook fails for a reason other than transient network.
7. The slice-id token collides with a prior shipped slice.
8. Any slice exceeds the scope budget (per `slice-delivery`; repo may override).
9. A slice subagent dies, stalls, or returns a report the orchestrator can't reconcile with the queue.
10. Operator interrupt (ctrl-C, explicit "stop" message).

When the loop stops, the next slice has NOT started. The repo is in a clean state (the just-shipped slice is merged/pushed; the in-flight slice does not exist yet, or its worktree is intact for inspection). Surface the reason for the stop in plain text — file paths, log excerpts, the exact failure mode.

## Final gate (after the queue is exhausted)

1. Run the full DOD check one last time, including any closeout-only bullets (e.g. no unpushed commits, hygiene thresholds).
2. Report the final state: starting pass count, ending pass count, slices shipped, slices stopped on, total commits.
3. If all DOD bullets PASS, state explicitly: `DOD GREEN — ship`. Do not say this otherwise.

## Related skills

Skills prefixed `superpowers:` are external plugin-namespaced skills that this skill composes when present. In an environment without them, treat each as "the repo-local equivalent if one exists, else inline the discipline manually."

- `slice-delivery` — the per-slice execution discipline every slice subagent runs.
- `superpowers:subagent-driven-development` — the dispatch pattern for per-slice subagents.
- `superpowers:using-git-worktrees` — isolation for parallel slice subagents.
- `superpowers:brainstorming` — invoked per-slice when design ambiguity exists.
- `superpowers:writing-plans` — invoked per-slice to produce the executable plan.
- `pr-discipline` — push/merge mechanics for PR-flow repos, layered between steps 4 and 5.
- `repo-hygiene` — closeout cleanup when the repo has no script of its own.
- `/loop` (harness skill) — optional cadence wrapper for re-entering the orchestrator on long queues; never a bypass for pause conditions.

## What this skill does NOT do

- Pick the next goal or author the DOD. That's the operator's call; the DOD arrives as input.
- Substitute for human design judgment on contested decisions. T0 will surface those; the operator resolves them.
- Run forever. The loop terminates when the queue is empty OR a hard stop fires. There is no retry loop on stops.
