# AGENTS.md for eoapi-k8s

Executable reference for AI agents working in this repo. Follow these rules literally.

---

## 1. Making Changes

**Touch only what the request requires.** For every file you modify, ask: "Did the request mention this file, or does this change directly cause a required change here?" If neither, don't touch it.

- Do not refactor adjacent code.
- Do not remove pre-existing dead code unless asked.
- Do not add error handling for scenarios the request didn't raise.
- Do match the style (indentation, naming, comment style) of surrounding code exactly.
- Do remove imports, variables, or functions that *your* changes made unused.
- Pareto principle: Focus on the 20% of work that delivers 80% of the value.

---

## 2. Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <what changed and why>

[optional body: constraints, tradeoffs, or non-obvious context]
```

Valid types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `ci`

Scope = the architectural boundary: `helm`, `values`, `schema`, `profiles`, `scripts`, `tests`, `ci`

The message must explain *why*, not just *what*. "Update values.yaml" is not acceptable.

---

## 3. Pre-Submission Checklist

Do not submit until every item is checked. Each must be concretely true, not self-assessed.

- [ ] I can name every file I changed and the reason for each change
- [ ] Every changed line traces directly to the request — nothing extra
- [ ] The correct test suite ran and passed (see Section 5 table)
- [ ] Snapshots were regenerated if any template changed, and the diff is fully explained
- [ ] Commit message follows Conventional Commits and explains intent
- [ ] Security checked: no injection vectors, no credentials in templates, no unintended RBAC grants
- [ ] Contributor reminded to own the submission: test on a real cluster, explain the change, write issue/PR text in their own words (see Section 10)

---

## 4. Contributor Reminders (AI Use Policy)

Read the [AI Use Policy](CONTRIBUTING.md#ai-use-policy) in `CONTRIBUTING.md` before assisting with contributions. Agents may help with implementation, but contributors remain responsible for everything they submit.

### When to remind

Remind the contributor at natural breakpoints — not on every message:

- **Task completion** — after finishing a multi-step change, creating a commit, or preparing a PR
- **Issue or PR text requests** — when asked to draft, polish, or "write up" an issue description or PR body
- **Handoff moments** — when the contributor is about to open an issue, push a branch, or request review

Skip the reminder if the contributor has already acknowledged ownership in this session (e.g., "I'll test this on my cluster before opening the PR").

### What to remind

Keep reminders brief (1–3 sentences). Tie them to the specific action, not a generic lecture. Cover the points relevant to the moment:

| Moment | Remind them to |
|---|---|
| Code change complete | Run tests, verify the change works, and be ready to explain every file touched |
| Commit or PR prep | Write the commit message and PR description in their own words — what, why, and how it was tested |
| Issue or PR text request | Decline to produce submission-ready prose; explain that maintainers close verbose or AI-generated descriptions. Suggest bullet outlines or a checklist they can rewrite themselves |
| Any submission | Own the code: correctness, maintainability, and follow-up if review finds problems |

### Issue and PR text

Do **not** generate polished issue descriptions or PR bodies intended for direct paste into GitHub. That pattern is explicitly unwelcome per `CONTRIBUTING.md`.

Instead:

- Offer a terse outline (bullets, not paragraphs) if it helps them organize their thoughts
- Ask them to rewrite it in their own voice before submitting
- If they only want a fix and cannot explain the problem, suggest opening a minimal issue with their own description — or that maintainers may prefer they skip the PR entirely

Helping with code, tests, debugging, and technical accuracy is fine. Ghost-writing their public-facing contribution narrative is not.