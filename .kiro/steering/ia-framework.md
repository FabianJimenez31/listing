---
inclusion: always
---

# IA-Framework: Project Constitution for Kiro

This workspace is governed by IA-Framework. The rules below are not suggestions;
local git hooks and CI enforce them, and work that ignores them will be blocked
at commit or push time.

## Use this project's spec layout, not Kiro's

**Do not create a Kiro spec tree.** This project already has one, and Kiro's
default artifacts collide with it — `tasks.md` is the same filename in both.

| Kiro default | Use instead |
|---|---|
| `requirements.md` | `specs/<slug>/spec.md` |
| `design.md` | `specs/<slug>/plan.md` |
| `tasks.md` | `specs/<slug>/tasks.md` |

Create a task with `make spec-new`, which generates the branch and the three
artifacts together. `<slug>` must match `NNN-kebab-case` (e.g. `001-user-login`)
and the branch must be `feature/<slug>`. The pre-commit hook verifies that all
three files exist and are filled in.

## Critical rules

- **File line limit**: no file over 1000 lines. Modularize at 800.
- **No scratch files in the repository root**: they belong in `temp/`.
- **Branch naming**: `(feature|fix|hotfix|chore|claude|codex|kiro|test)/<slug>`.
  Direct commits or pushes to `main`, `master` or `develop` are blocked.
- **No hardcoded secrets**: the secret scanner blocks the commit, and it is
  never skipped, not even under an emergency bypass.

## Memory Protocol

This project has persistent memory through Engram. Memory is written by the
harness, not by you: git hooks and agent hooks persist it over Engram's local
HTTP API. You are not responsible for saving it, and you should not assume a
`mem_save` call is what keeps it alive.

**You are responsible for reading it.** Before drafting a plan, changing
architecture, or proposing an approach, search memory for the task slug and for
the components you are about to touch. The project has already decided things,
and re-deciding them is the failure mode this exists to prevent.

Seven classes are tracked per task:

| Class | Where it lives | Written when |
|---|---|---|
| Contextual | Engram session | `make spec-new` |
| Episodic | Session timeline | Automatically |
| Semantic | `spec/<slug>/semantic` | `plan.md` is completed |
| Procedural | `spec/<slug>/procedural` | `tasks.md` is completed |
| Decision | `spec/<slug>/decision` | Every commit |
| Preferences | `user/preferences` | The user states a constraint |
| Outcome | `spec/<slug>/outcome` | Push, CI, or hotfix |

Quotas scale with the branch prefix: `feature/` requires all seven, `fix/` and
`hotfix/` require three (decision, outcome, semantic recorded as `bugfix`), and
`chore/` requires one (decision). The gate runs at push time and blocks.

If the user states a working constraint that should outlive this session, record
it explicitly:

```bash
bash scripts/memory/capture_stage.sh preferences "<the constraint>"
```

## Commands

| Command | Purpose |
|---|---|
| `make spec-new` | Create a feature branch with its spec artifacts |
| `make dev-check` | Run local quality gates before committing |
| `make mem-context` | Show what the project already remembers |
| `make mem-check` | Evaluate the memory quota for this branch |
| `make mem-doctor` | Diagnose the memory subsystem |
| `make test` | Run the test suite |
