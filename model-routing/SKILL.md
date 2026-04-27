---
name: model-routing
description: Decide which model, thinking level, and review lane to use when delegating to another agent/session, scheduling agent jobs, or choosing a model for implementation/review/docs/triage. Use before any explicit model choice or when asked which model to use.
---

# Model Routing

Use this skill to pick the cheapest model that is likely to succeed, while preserving independent review for risky work. Treat the concrete model names below as examples; adapt them to the models, quotas, and providers available in the current environment.

## Inputs to gather

- Task class: implementation, review, docs, triage, architecture, cleanup, monitoring.
- Scope: single file, multi-file, cross-repo, long-running/autonomous.
- Risk: auth, payments, messaging/send paths, data migrations, security, production infra, observability contracts.
- Context size: small (<50k), medium (50–150k), large (>150k), huge (>250k).
- Cost/quota shape: flat-rate, metered, throttled, separate quota.

## Example tier map

Customize this map for the local environment before relying on it:

| Lane | Example model shape | Use for |
|---|---|---|
| Fast lane | fastest cheap coding model, low/medium thinking | tiny edits, docs nits, formatting, search-and-replace |
| Default implementation | default coding model, medium thinking | mechanical implementation from a tight spec |
| Strong implementation | stronger coding model, medium thinking | multi-file or longer-horizon implementation |
| Review/judgment | strongest same-family model, high thinking | adversarial review, architecture, unclear requirements |
| Emergency/off-family | different provider/model family, high thinking | highest-risk review or tie-break when same-family models disagree |

## Default routing pattern

| Task | Recommended lane |
|---|---|
| Tiny targeted edits, obvious docs nits, formatting, renames | fastest cheap model, low/medium thinking |
| Mechanical implementation from tight spec | cheap/default coding model, medium thinking |
| Well-scoped multi-file implementation | stronger coding model, medium thinking |
| Long-horizon autonomous loop | stronger model, medium/high thinking |
| Non-trivial code review | stronger model than implementer, high thinking, adversarial prompt |
| RFC / architecture / unclear requirements | strongest available reasoning model, high thinking |
| Highest-risk review | off-family model if available, high thinking |

## Escalation ladder

1. Start with the cheapest lane that matches the task and context.
2. If it fails, decide whether the failure was **spec weakness** or **model weakness**.
3. If spec weakness: tighten acceptance criteria and retry same lane once.
4. If model weakness: escalate one tier.
5. For risky changes, add review rather than simply escalating implementation.

## Review decorrelation

Never review substantial work with the same model + same thinking level + same prompt frame that wrote it.

At minimum change two of:
- model tier
- thinking level
- prompt frame: constructive implementation vs adversarial review
- provider/model family

Adversarial review prompts should ask for:
- production-realistic failure modes
- invariants preserved by old code
- silent failure modes
- weakened tests or assertions
- missing rollback / migration / observability coverage

## Prompt discipline for cheaper lanes

Cheaper/faster models need tighter specs:
- exact files or search targets
- acceptance criteria
- test command(s)
- expected output format
- explicit non-goals
- whether to open a PR, commit, or only report

Avoid vague prompts like “investigate and fix”. Prefer “change X so Y passes; run Z; report diff + test result”.

## Spawn checklist

Before delegating:

1. Pick lane from table.
2. Set model and thinking explicitly.
3. Use an isolated worktree if parallel agents may touch the same repo.
4. Include acceptance criteria and verification commands.
5. Decide review lane now for non-trivial work.
6. State stop conditions: when to ask, when to escalate, when to only report.

## Anti-patterns

- Using a premium model for obvious mechanical edits.
- Using the same lane for implementation and review.
- Escalating because the prompt was vague.
- Delegating risky auth/payment/messaging/schema work without independent review.
- Letting fast models run broad autonomous tasks without tight boundaries.
