# Quality Checklist: Pre-Merge / Pre-Deploy

Before requesting a code review, merging a Pull Request, or promoting changes to staging/production, verify that this checklist is fully satisfied.

## 🛠️ Local Quality Gate (Local Machine)
- [ ] **Tests pass:** The full suite of local tests passes successfully.
  * *Command:* `make test` or equivalent.
- [ ] **Code limits respected:** No new files exceed the 1000-line limit, and modified files are modular and highly cohesive.
  * *Command:* `make dev-check`
- [ ] **No temporary files:** No backup files, logs, or debugging scripts (`.py`, `.sh`, `.log`) exist in the project root.
- [ ] **Secrets scanned:** Confirmed that no passwords, private API tokens, or credentials are hardcoded.

## 🔗 Architecture & Integrations
- [ ] **Multi-tenant isolation:** All database queries and context access filters by tenant/user id where applicable.
- [ ] **No breaking changes:** Database migrations are backwards-compatible and schema modifications have been fully tested.
- [ ] **Log clean-ups:** Ensure heavy console logs or debugging print statements are removed before commit.

## 🏗️ Spec-Kit Compliance
- [ ] **Specs matched:** The current branch name corresponds perfectly to the `specs/<slug>/` folder.
- [ ] **Documentation updated:** The `spec.md`, `plan.md`, and `tasks.md` files are completely updated and match the actual implementation.
