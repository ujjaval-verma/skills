---
name: model-routing
description: Decide which model and thinking level to use when spawning a sub-agent, delegating implementation, reviewing a PR, writing an RFC, doing CI/tooling work, authoring docs, or otherwise choosing a model for non-main work. Use when about to call sessions_spawn, subagents(action=steer), cron add with payload.kind=agentTurn, or any moment the model is an explicit choice. Covers openai-codex/gpt-5.4 and openai-codex/gpt-5.5 in a GPT-only routing setup. Triggers on phrases like "spawn", "subagent", "meta-review", "review PR", "delegate", "routing decision", "which model", "escalate to bigger model".
---

# Model Routing

GPT-only routing. Anthropic is disabled; do not route work there. Opus is not used.

## Golden rules

1. **Main session: GPT-5.5 high.** This is the default and preferred main-thread mode.
2. **Sub-agent default: GPT-5.4 medium.** Use for mechanical work and tight specs.
3. **Long-horizon / multi-file / former-Sonnet-class subagents: GPT-5.5 medium.** Escalate when 5.4 medium will run out of coherence.
4. **Use GPT-only.** Do not route work to Anthropic models.
5. **Never meta-review with the same model + same thinking level that wrote it.** Decorrelate with a different thinking level and an adversarial prompt frame.
6. **Tight task specs matter more as you go cheaper.** GPT-5.4 rewards concrete acceptance criteria.
7. **Never use Opus.**

## Decision matrix

| Task class | Model | Thinking |
|---|---|---|
| Main session orchestration | `openai-codex/gpt-5.5` | `high` |
| Mechanical impl from tight spec | `openai-codex/gpt-5.4` | `medium` |
| Doc authoring from a brief | `openai-codex/gpt-5.4` | `medium` |
| Well-scoped follow-up PRs | `openai-codex/gpt-5.4` | `medium` |
| Trivial meta-reviews | `openai-codex/gpt-5.4` | `medium` |
| Simple fixes during hardware/live testing | `openai-codex/gpt-5.4` | `medium` |
| First attempt at a fuzzy task | `openai-codex/gpt-5.4` | `medium` → escalate on failure |
| Long-horizon autonomous lanes | `openai-codex/gpt-5.5` | `medium` |
| Multi-file impl from spec (>3 files, sequential dependencies) | `openai-codex/gpt-5.5` | `medium` |
| Non-trivial meta-review (>100 lines, runtime-behavior PRs, >5 files, call-graph reasoning) | `openai-codex/gpt-5.5` | `high` |
| RFC / architecture design | `openai-codex/gpt-5.5` | `high` |
| Security-sensitive first impl, complex multi-file refactor with non-obvious call-graph | `openai-codex/gpt-5.5` | `high` |

## Escalation ladder

```text
GPT-5.4 medium
    ↓ scope grows / first attempt failed / multi-step
GPT-5.5 medium
    ↓ judgment depth / >200k context / non-trivial meta-review
GPT-5.5 high
```

## Combo pattern — GPT-only edition

1. **Impl spawn** — GPT-5.4 medium (mechanical) or GPT-5.5 medium (multi-file/long-horizon) with a tight constructive task spec.
2. **Meta-review spawn** — GPT-5.5 high with an adversarial prompt frame.
3. Merge when meta-review approves.

With GPT-only, the adversarial review prompt matters more. Don’t skip it.

## Anti-patterns

- Reaching for Opus.
- Defaulting away from GPT for judgment work.
- Reflexively promoting 5.4 work to 5.5 when 5.4 is enough.
- Skipping the adversarial review pass on non-trivial PRs.
- Vague task specs with cheap models.
- Same model + same thinking level for impl and review.
- `thinkingDefault` mismatches. GPT models use `low` / `medium` / `high`.

## Spawn-time checklist

1. What task class from the matrix above?
2. Does the task need long-horizon coherence? If yes → GPT-5.5 medium minimum.
3. Does the task need judgment / adversarial review? If yes, plan the GPT-5.5 high review pass now.
4. Is the spec tight enough for a cheaper model? If no, tighten it before spawning.
5. What’s the fallback if the spawn fails? Usually: re-spawn one tier up.
6. **Working-dir isolation** — if running ≥2 sub-agents in parallel on the same repo, each must get its own `git worktree` under `~/src/<repo>-WORKTREE-N/`. Never `/tmp/`.

Then set `model:`, `thinking:`, and `cwd:` explicitly in the spawn call.

## Examples

- Mechanical bug-bash bursts — GPT-5.4 medium impl, GPT-5.5 high adversarial review.
- Long autonomous lanes — GPT-5.5 medium impl, GPT-5.5 high adversarial review.
- RFC / architecture brief — GPT-5.5 high directly.
- Auth/SMS-send/schema PR — GPT-5.5 medium impl → GPT-5.5 high adversarial review.

## Escalation on failure

1. Re-read the output. Was the failure spec weakness or model weakness?
2. If spec: tighten and re-spawn on GPT-5.4 high or GPT-5.5 medium as needed.
3. If model: re-spawn on GPT-5.5 medium or high.
4. If GPT-5.5 also fails: split the task and retry.

## Pricing intuition

- GPT-5.4 marginal: subscription / flat
- GPT-5.5 marginal: subscription / flat
- Opus: removed from routing

Keep everything on GPT-5.4/5.5 and avoid Anthropic entirely.

## Auto-compaction

Auto-compaction is on at the agent level via `agents.defaults.compaction` in `~/.openclaw/openclaw.json`.
