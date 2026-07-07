# Refactor-scan candidate catalogue

Disclosed reference for [`slice-delivery`](../SKILL.md). Consulted during the **refactor scan** that runs after every green test — not loaded with the skill body.

Run the scan on the code you just changed and its immediate neighbours. Candidates:

- **Duplication** → extract function / value object.
- **Long methods** → break into private helpers (tests stay on the public interface).
- **Shallow modules** → combine or deepen.
- **Feature envy** → move logic to where the data lives.
- **Primitive obsession** → introduce a typed value.
- **What does new code reveal about existing code?** — the most powerful candidate. Your new code often makes a previously-tolerable wart obvious. Fix it now, in this slice, as a separate commit. Do not accumulate a cleanup PR backlog.

Refactors are separate commits from features. Refactor-then-feature is two commits.
