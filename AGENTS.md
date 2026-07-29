# Listing — Project Constitution (CLAUDE.md / AGENTS.md)

This document guides developers and AI assistants (Claude, GPT, Gemini, etc.)
working on **Listing**. It defines the architectural boundaries, coding
guidelines, and the quality gates enforced by the IA-Framework harness.

Project context: a Python project bootstrapped with the IA-Framework
spec-driven quality harness. SonarQube runs locally in Docker for the Quality
Gate (see "Tooling" below).

## 🚨 Critical Rules

- `File Line Limit (1000 lines)`: **Strict Rule**. No single file may exceed 1000 lines. When approaching 800 lines, stop, modularize, and divide functionality. The hook `.claude/hooks/check-file-size.sh` blocks writes that violate this.
- `Zero Temporary Files in Root`: All temporary, scratch, and debug scripts must reside in `temp/` subdirectories. The pre-commit hook blocks any violation of this.
- `Feature Branch Convention`: All development must be done on branches starting with standard prefixes: `(feature|fix|hotfix|chore|claude|codex|test)/[name]`. Direct push/commit to `main`, `master`, `staging`, or `develop` is strictly blocked — changes land on `main` only via reviewed Pull Requests.
- `Specification-Driven Development`: Feature branches must have their corresponding design specifications before development. The pre-commit hook verifies that `specs/<slug>/{spec.md,plan.md,tasks.md}` exist and are filled out.
- `No Generic Dump Modules`: Files named `utils.py`, `helpers.py`, `common.py`, `misc.py`, `temp_*.py`, `new_*.py` are blocked by `scripts/validation/validate_structure.py`. Create focused, named modules instead (e.g. `listing_catalog.py`, `price_formatter.py`).
- `No Hardcoded Secrets`: Committing api keys, tokens, or credentials will be blocked by the secret scanner. Use `.env.local` (git-ignored); see `.env.example`.

## 🏗️ Architecture Summary

Current layout (kept flat and focused — grow by **domain capability**, not by generic layers):

- **`src/`**: Application source code (a Python package).
  - Modules are small, single-responsibility files. Today: `listing_catalog.py` (listing domain model + `ListingStatus` enum + in-memory `Catalog`).
  - As the codebase grows, group related modules by capability (e.g. `catalog/`, `pricing/`, `inventory/`). Do **not** introduce `models/`/`services/`/`api/` shells until there is real code to fill them.
- **`tests/`**: Pytest suite. Markers: `unit`, `integration`, `critical` (see `pytest.ini`). Mirrors `src/` module names (`test_<module>.py`).
- **`specs/`**: One folder per feature (`specs/<slug>/{spec.md,plan.md,tasks.md}`).
- **`scripts/`**: `validation/` (structure, enums), `harness/` (sonar server, nginx lint, SPA smoke), `deployment/` (hotfix, rollback).
- **`temp/`**: Scratch, logs, backups, emergency logs (git-ignored subdirs).

## 🛠️ Developer Workflow

1. **Initialize Feature:** Run `make spec-new` to create a `feature/<NNN-slug>` branch and pre-populate `specs/<slug>/`.
2. **Design Specifications:** Define requirements in `spec.md` and technical strategy in `plan.md`. Get review before writing code.
3. **Develop & Implement:** Write focused code in `src/`, tests in `tests/`. Track progress in `tasks.md`.
4. **Local Verification:** Run `make dev-check` (hooks) and `make test` (pytest). Optionally `make sonar-check` for the local Quality Gate.
5. **Push and PR:** Push the branch (pre-push runs the test suite), open a Pull Request, ensure CI gates are green, merge to `main`, and clean up.

## 🔌 Tooling — SonarQube Quality Gate

- **Local server (Docker):** `make sonar-up` starts SonarQube on `http://localhost:9000`, provisions a token, and writes `SONAR_HOST_URL` / `SONAR_TOKEN` to `.env.local`. `make sonar-down` removes it.
- **Run the gate:** `make sonar-check` (tests + coverage → scanner → poll Quality Gate). Config in `sonar-project.properties` (`projectKey=listing`).
- **CI:** `.github/workflows/ci-quality-gate.yml` runs the remote gate when `SONAR_HOST_URL` + `SONAR_TOKEN` repo secrets exist (a localhost server is not reachable from GitHub runners — point CI at a hosted SonarQube/SonarCloud).

## ⏩ Operations & Emergency Procedures

- **Database-Code Enum Sync:** `make validate-enums` checks DB records vs code Enums. ⚠️ Currently a **generic demo** and the pre-commit enum gate is **disabled** until the database schema and domain Enums are defined (wire `scripts/validation/validate_enums.py` to the real DB, then re-enable the hook in `.pre-commit-config.yaml`).
- **Nginx Config Sanity Gate:** `make lint-nginx` — only relevant once an Nginx/proxy layer exists.
- **Frontend SPA Smoke Tester:** `make smoke-test` — only relevant once a deployed SPA frontend exists.
- **Incident & Emergency Hotfixes:** `make hotfix` generates docs in `temp/emergency_logs/`, snapshots state in `temp/backup/`, and uses the `HARNESS_EMERGENCY=1` bypass.
- **Atomic Rollback & Recovery:** `make rollback` lists git safety tags and patches; `scripts/deployment/rollback.sh apply <target>` restores state.
