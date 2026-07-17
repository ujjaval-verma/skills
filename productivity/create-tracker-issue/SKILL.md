---
name: create-tracker-issue
description: Draft and file a terse, well-shaped issue in whatever tracker is at hand (Jira, Linear, GitHub Issues, …). Use for ad-hoc issue creation — "file a ticket", "create an issue", "log a bug", "write this up as a story" — outside any delivery workflow.
updated: 2026-07-17
---

# Create tracker issue

Author a terse, specific issue and file it in whichever tracker the environment offers. This skill owns the content shape only — not slice sequencing, delivery workflow, or project-management judgment.

## Template

At most four sections, in this order. **Title + Acceptance Criteria is a valid complete issue.** An absent section beats an empty or padded one.

| Section | Carries | Include when |
|---|---|---|
| **Objective** (why) | The problem and the user/business value, 1–2 sentences max. | The why isn't evident from the title. |
| **Context** (what) | High-level overview of the change; links to designs / Figma / API specs; step-by-step repro for bugs. | There's something concrete to carry — a repro, a link, a non-obvious constraint. |
| **Acceptance Criteria** (when is it done) | Bulleted, verifiable requirements defining the exact boundary of the task. | **Always.** |
| **Technical Notes** (how) | Suggested approach, files/endpoints to touch, known dependencies, blockers, security risks. | Only when a single sensible approach, dependency, or risk is already known. Skip for spikes, discovery, or anything vague by design. |

Writing rules:

- Specificity over template-filling; less is more. No "As a user, I want…" boilerplate — the section structure *is* the story pattern.
- Every Acceptance Criteria bullet must be verifiable by someone other than the author (a QA engineer could turn it into a test case).
- Technical Notes are hints, not mandates — leave the section flexible for the developer.

## Flow

1. **Draft.** Write the issue in Markdown using the template and show it to the user.
2. **Identify the tracker.** In order: explicit user statement → tools present in the environment (Linear/Jira MCP tools, `gh` with a GitHub remote) → ask, only if still ambiguous.
3. **Fill required fields only.** Ask once for tracker-required fields you can't infer (team, project, issue type, repo). Never invent optional metadata — labels, priority, estimate, assignee are set only when the user supplied them.
4. **Create on confirmation.** Filing the issue is an external write — confirm draft + destination before creating. If no tracker tooling is available, hand over the Markdown for manual pasting and stop.

## Example (minimum viable issue)

> **Title:** Rate-limit password reset emails
>
> **Acceptance Criteria**
> - At most 3 reset emails per address per hour; requests beyond the limit return the normal success response (no account-enumeration signal).
> - The limit is per-address, not per-IP.
> - Covered by a test; existing reset-flow tests still pass.

No Objective (the title carries the why), no Context (nothing concrete to link), no Technical Notes (multiple valid implementations).
