# Contributing

Thanks for considering a contribution. This repo holds **reusable, repo-agnostic AgentSkills** — small Markdown files that teach a coding agent how to do one thing well. Keep that in mind: every skill you add or edit should be usable from *any* repo, not just yours.

If you've never written an AgentSkill before, skim the [README](README.md) and one or two existing skills (e.g. [`engineering/pr-discipline/SKILL.md`](engineering/pr-discipline/SKILL.md)) before opening a PR.

## Ground rules

1. **One concern per PR.** Add one skill, rename one skill, or fix one bug — not all three. Small PRs land; large ones rot.
2. **Branch protection is on.** `main` requires a pull request and a linear history. No direct pushes, no force-pushes, no branch deletions.
3. **No secrets, no private paths.** No tokens, internal hostnames, user home directories, or repo-specific assumptions unless the skill is explicitly scoped to that repo. See [README → What not to include](README.md#what-not-to-include).
4. **Follow Conventional Commits.** Scope by category or skill name: `feat(slice-delivery): …`, `docs(readme): …`, `refactor(linear-sop): …`. See `git log` for examples.
5. **Adversarial review for non-trivial changes.** Any change beyond a typo, link fix, or single-line config tweak must show an adversarial review trail before merge. See [`CLAUDE.md` → Adversarial review (Ralph) — contract](CLAUDE.md#adversarial-review-ralph--contract).

## Adding a new skill

1. **Pick the right category.** `engineering/`, `product/`, or `productivity/`. If none fit, open an issue first — adding a category is a design decision.
2. **Create a hyphen-case folder** under the category whose name matches the `name:` you'll put in frontmatter. Folder name and `name:` must never drift.
3. **Write `SKILL.md`** with the frontmatter block:

   ```yaml
   ---
   name: example-skill
   description: Trigger-oriented description — when an agent should invoke this skill.
   updated: YYYY-MM-DD        # ISO date of last material edit
   wave: <int>                # optional; only if part of a deliberate refactor wave
   ---
   ```

4. **Keep the body focused** on reusable workflow instructions. Cut prose the agent already knows without the skill present. If the skill needs a helper script, drop it under `<skill-name>/scripts/` and reference it by relative path from `SKILL.md`. Don't add a `scripts/` folder speculatively.
5. **Update both lookup surfaces in [`README.md`](README.md)** in the same PR — the **Skills** table (the canonical "what does it own?" index) *and* the **Triggers** table (the "what should I say to invoke it?" quick reference). Folder, `name:`, and both table entries always move together.
6. **Cross-references count too.** If you rename a skill or change its scope, update every `Related skills` line and delegation pointer in other skills in the same PR.

## Editing an existing skill

- Bump `updated:` in the frontmatter when the body changes materially. Typo and link fixes don't count.
- Don't assign `wave:` retroactively. A wave is only meaningful when paired with a defined refactor cohort.
- If the change is non-trivial, post an adversarial review trail (see [`CLAUDE.md`](CLAUDE.md#adversarial-review-ralph--contract)).

## Workflow

```bash
git checkout -b <kebab-case-branch>
# edit
git commit -m "feat(<scope>): <imperative summary>"
git push -u origin HEAD
gh pr create --fill
```

CI is lightweight today (social enforcement); future lint may enforce frontmatter shape. Don't bypass hooks or branch protection.

## Reporting issues

Open a GitHub issue with:
- What you tried to do.
- The skill (or missing skill) involved.
- What the agent did instead, with enough context to reproduce.

## Code of conduct

Be kind, be specific, assume good faith. Disagreement is fine; performative agreement is not.

## Maintainer notes

### Regenerating the social card

The repo's GitHub social preview is uploaded manually via repo **Settings → Social preview** (no public API). Source SVG (`docs/assets/social-card.svg`) and the rendered 2:1 JPG (`docs/assets/social-card.jpg`) live together; the SVG is intrinsically 1280×640 (2:1) with all content kept inside GitHub's 40pt safe-area inset, so the regen is a one-shot screenshot at 2× pixel density. Run from repo root:

```bash
# macOS — Chrome + sips
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --window-size=2560,1280 --screenshot=/tmp/card.png \
  "file://$PWD/docs/assets/social-card.svg"
sips -s format jpeg -s formatOptions 92 /tmp/card.png --out docs/assets/social-card.jpg
```

On Linux, swap `sips` for ImageMagick: `convert /tmp/card.png -quality 92 docs/assets/social-card.jpg`.

If you reflow the SVG, keep meaningful content inside the safe area (40pt inset → coordinates `[40,40]` to `[1240,600]` in the 1280×640 viewBox) so GitHub's bleed crop doesn't clip anything important.
