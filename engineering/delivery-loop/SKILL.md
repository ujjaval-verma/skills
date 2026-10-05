---
name: delivery-loop
description: Multi-slice autonomous delivery wrapper around slice-delivery — operator-invoked loop that ships a pre-flight slice queue against a supplied Definition of Done via per-slice subagents.
disable-model-invocation: true
updated: 2026-10-04
---

# Delivery loop

Runs `slice-delivery` across a queue of slices with no human approval between slices, for sessions where the operator has already pinned the design (ADRs, invariants, a Definition of Done). It composes `slice-delivery`; it does not replace it. Each slice still runs that skill's start-lane gate and lifecycle gate, and `pr-discipline` owns PR mechanics. For one slice, invoke `slice-delivery` directly.

Added here: a pre-flight queue, a T0 spec-review gate per slice that substitutes for human approval, hard pause conditions, a regression floor, and a final DOD gate.

## The DOD is an input

The operator must supply a Definition of Done, inline (acceptance bullets) or by reference (a path or URL, ideally with the command that checks it, "the DOD harness"). With none supplied or confirmed at a conventional location, refuse to start: without a DOD the loop has no termination condition and no regression floor. Never synthesize one mid-loop; proposing a DOD is its own human-gated task.

With bullets but no harness, the regression gate becomes a bullet-by-bullet check recorded in the slice's PR or commit. Say which mode you are in during pre-flight.

## Preconditions

Refuse to start, naming the missing item, if any is absent. Never bootstrap one mid-loop; that is its own slice.

- A DOD (above).
- Invariants, architecture notes or ADRs in tracked locations, or the operator's explicit "no invariants exist yet".
- A spec-review template, else use `slice-delivery`'s T0 lenses.
- Explicit operator invocation.

## Pre-flight (once, before slice 1)

1. **Queue.** Use the operator's named slices in the given order; otherwise walk unmet DOD bullets in dependency order, unblocked first.
2. **Dump the queue** to stdout before starting: slice-id, one-line scope, source bullets, estimated task count, then "Starting shortly — interrupt to revise." Pause for the interrupt window.
3. **Slice-id collision check.** Grep `git log origin/<default-branch>` for each slice-id scope token. On any hit, stop and ask the operator to disambiguate.
4. **Baseline the DOD.** Run the harness and record the pass count (or which bullets are met). This is the regression floor: it only rises, never drops.

## Subagents

The orchestrator never reads diffs. Each slice and each reviewer is a fresh subagent, and reviewers never share context or authorship with what they review. Run slices sequentially unless they are provably independent (no shared files or DOD bullets) and each has its own worktree.

## Per-slice loop

1. **Spec and plan.** Draft per `slice-delivery` (brainstorm first only if the design is ambiguous).
2. **T0 spec-review** per `slice-delivery`'s start lane. Mandatory in the loop, never skipped: it stands in for human approval. Branch on the report:
   - All "None." Proceed.
   - BLOCKING, all mechanical (missing cross-reference, inconsistent field name, non-scope clarification, typo in a verification criterion). Patch the spec or plan, record dispositions, re-run T0 once. If BLOCKING survives, treat as non-mechanical.
   - BLOCKING that is not mechanical (invariant violation, ADR contradiction, scope past budget), or a lens-B DEFERRED value judgment. Stop the loop and surface it with the review artifact path; the subagent cannot make this call, the operator can.
3. **Implement.** Dispatch a fresh subagent with the approved spec and plan, the DOD and its worktree. It runs the `slice-delivery` lifecycle, including its Ralph step (every loop slice counts as non-trivial), with one exception: if the first Ralph pass returns more than 1 BLOCKING, it stops before fixing or merging and returns to the orchestrator (pause 3). It reports slice-id, what shipped, verification evidence, dispositions and anything that smells like a pause condition; the orchestrator, not the subagent, decides whether to continue.
4. **Regression gate.** After the slice lands (`pr-discipline`), run the DOD check against the baseline. At or above it, raise the baseline and continue. Below it, stop: a previously met bullet regressed, so surface the DOD diff and do not start the next slice.
5. **Close out.** Fold transient artifacts per the repo's disposition rubric, run its hygiene script (else `repo-hygiene`), and keep a one-paragraph summary.

For long queues, `/loop` may re-enter the orchestrator on a cadence; it never bypasses a pause condition.

## Pause conditions (hard stops, no recovery loop)

Stop immediately and surface to the operator when:

1. T0 returns BLOCKING that survives one mechanical retry.
2. T0 returns a lens-B DEFERRED value judgment.
3. The slice's first Ralph pass returns more than 1 BLOCKING finding; the slice stops before it merges (one is normal mid-slice; a cascade means something deeper is wrong).
4. The DOD check regresses below the baseline.
5. The slice-id collides with a prior shipped slice.
6. A slice exceeds the scope budget (per `slice-delivery`).
7. A slice subagent dies, stalls, or returns a report the orchestrator cannot reconcile with the queue.

On a stop the next slice has not started, shipped slices are pushed, and any in-flight worktree is left intact for inspection.

## Final gate

1. Run the full DOD check once more, including closeout-only bullets (no unpushed commits, hygiene thresholds).
2. Report starting and ending pass counts, slices shipped, slices stopped on, and total commits.
3. If every bullet passes, state `DOD GREEN — ship`. Say it only then.

## Related skills

`slice-delivery` (per-slice discipline), `pr-discipline` (push and merge), `repo-hygiene` (closeout), `superpowers:subagent-driven-development`, `superpowers:using-git-worktrees`, `superpowers:brainstorming`, `superpowers:writing-plans` (used when installed, else the repo-local equivalent).
