# IA-Framework: Spec-Kit & Quality Gate Harness

**IA-Framework** is a turnkey boilerplate that implements a professional, rigorous, and automated development workflow. It combines **Specification-Driven Development (Spec-Kit)** with strict **Quality Gate Harnesses** (Git Hooks + GitHub Actions CI) to enforce high-quality standards and protect codebases from agent drift, code bloat, and regression.

Perfect for modern engineering teams and developers paired with AI coding assistants (Claude Code, GPT, Gemini, etc.).

---

## 🚀 Key Features

*   **Specification-Driven Development (Spec-Kit):** Enforces that coding *only* begins after requirements, technical strategy, and task checklists are explicitly defined and placed in `specs/<slug>/`.
*   **AI Code Safeguards:** Blocks AI assistants from writing bloated code by enforcing a strict **1000-line limit** per single source file (warns at 800 lines).
*   **Strict Local Git Hooks:**
    *   Hard-blocks direct commits or pushes to protected branches (`main`, `master`, `develop`, etc.).
    *   Validates Git Flow branch naming conventions (`feature/`, `fix/`, `hotfix/`, `chore/`).
    *   Scans diffs for hardcoded secrets, api keys, and private tokens.
    *   Forces cleanup of temporary Python/shell scripts in the repository root.
*   **Boilerplate CI/CD Quality Gates:** Generic GitHub Actions workflows to validate file sizes, branch naming, and run automated test suites on every Pull Request.
*   **Advanced Operations & Harness Suite:**
    *   **Nginx Upstream Linter:** Blocks IPv6 connection lottery hazards in proxy/upstream routing configurations (localhost loops).
    *   **Frontend SPA Smoke Tester:** Guarantees atomic deployment states, ensuring that all SPA routes are up and reference identical static bundle versions.
    *   **Database-Enum Integrity Checker:** Performs set checks between code Enums and raw database distinct records to avoid runtime data degradation.
    *   **Structured Incident & Hotfix Pipelines:** Standardizes emergency responses with automated backups, local testing gates, rollback tags, and incident documentation logs.
*   **Developer CLI API & Pre-Commit Config:** A clean `Makefile` and `.pre-commit-config.yaml` providing standard endpoints for all local quality gates and workflow tasks.

---

## 📁 Directory Structure

```text
.
├── .specify/                         # 🛠️ Spec-Kit templates & CLI scripts
│   ├── templates/                    # Markdown templates (Spec, Plan, Tasks)
│   └── scripts/bash/                 # Automation scripts for branches/validation
├── .claude/                          # 🤖 AI Agent Safeguards & Git Hooks
│   └── hooks/                        # Pre/Post hooks & hook wrappers
├── .github/workflows/                # 🔗 CI/CD pipeline quality gates
├── scripts/                          # ⏩ Custom project-specific validation & ops
│   ├── validation/                   # Architecture & Database-enum consistency validators
│   ├── harness/                      # Web server & Deployment smoke checkers
│   └── deployment/                   # Standard emergency hotfix & rollback scripts
├── temp/                             # 📂 Organized playground for scrap/logs
├── .pre-commit-config.yaml          # 🔗 Git pre-commit framework config
├── Makefile                          # Unified CLI commands for developers
├── install.sh                        # One-click interactive installer
├── CLAUDE.md                         # Reference project constitution for AI
├── AGENTS.md                         # Reference mirror for other AI assistants
└── README.md                         # This file
```

---

## ⚡ Quick Start & Installation

To integrate **IA-Framework** into any existing or new project:

1.  **Clone or Copy** the framework files into the root of your project repository.
2.  Run the **One-click Installer**:
    ```bash
    chmod +x install.sh
    ./install.sh
    ```
    This script will:
    *   Initialize Git (if not already done).
    *   Establish folders (`specs/`, `temp/`, `src/`, `tests/`, `scripts/`).
    *   Automatically bind local Git hooks to `.claude/hooks/git` using Git `core.hooksPath`.
    *   Populate the `.gitignore` with standard rules.
    *   Generate your `CLAUDE.md` and `AGENTS.md` constitution guidelines.

3.  Verify the installation:
    ```bash
    make help
    ```

---

## 🛠️ Developer Workflow

The framework implements a highly reliable TDD-like cycle powered by specifications:

### 1. Initialize a Feature
Run the following command to interactively create a new feature branch and pre-populate specification templates:
```bash
make spec-new
```
*   *Prompt example:* `001-user-login`
*   *Result:* Creates branch `feature/001-user-login` and initializes files:
    *   `specs/001-user-login/spec.md` (Product/Business specifications)
    *   `specs/001-user-login/plan.md` (Technical implementation plan)
    *   `specs/001-user-login/tasks.md` (Checklist to track implementation progress)

### 2. Design Phase
Document your business requirements in `spec.md`, design your architecture and dependencies in `plan.md`, and outline tasks in `tasks.md`.

### 3. Development Phase
Implement the code (e.g. in `src/`). Track progress by updating the `[ ]`, `[/]`, and `[x]` states inside `tasks.md`.

### 4. Local Validation Gate
Before committing, verify that your changes pass all local hooks:
```bash
make dev-check
```
*   This will check branch naming, verify that spec files exist, scan for secrets, run the Python architecture anti-pattern scanner, and block files that exceed 1000 lines.

### 5. Push & Pull Request
Push your branch and open a Pull Request. The **CI Quality Gate** will automatically run remote checks. Once green, merge to `main` and enjoy clean, high-quality code!

---

## ⏩ Operations & Emergency Procedures

IA-Framework comes preloaded with production-tested developer operations scripts.

### 📊 Database-Code Enum Validation
To check database record consistency vs. code Enum classes, run:
```bash
make validate-enums
```
This runs `scripts/validation/validate_enums.py`, which computes exact set differences and suggests updates before discrepancies cause validation crashes.

### 🌐 Nginx Config Upstream Linter
To verify active Nginx sites and prevent the IPv6/IPv4 localhost connection lottery bug, run:
```bash
make lint-nginx
```
This runs `scripts/harness/lint_nginx.sh` to parse configs and enforce explicit IP targets (`127.0.0.1`).

### 📦 Frontend SPA Smoke Testing
To run an automated post-deploy smoke test checking route status and JS chunk versions compatibility (atomic checks), run:
```bash
make smoke-test
```
This runs `scripts/harness/smoke_test_frontend.sh`. You can configure it by setting environment variables:
```bash
BASE_URL=https://myprodapp.com ROUTES="/ /dashboard /admin" make smoke-test
```

### 🚨 Structured Production Emergency Hotfix
When production is down and normal staging review stages must be bypassed, run:
```bash
make hotfix
```
This will run the interactive hotfix initializer `scripts/deployment/emergency_hotfix.sh crear`:
1.  **Safety Snapshots:** Saves dirty changes into `temp/backup/`.
2.  **Incident Documentation:** Creates a post-mortem Markdown template in `temp/emergency_logs/` so that fixes are documented.
3.  **Emergency Validation:** Run `scripts/deployment/emergency_hotfix.sh validar` to run local tests.
4.  **Bypass Action:** Run `scripts/deployment/emergency_hotfix.sh aplicar` to commit/push the fix using the `HARNESS_EMERGENCY=1` bypass.

### ⏪ Atomic Local & Git Rollback
If a hotfix or deploy causes unforeseen regressions, run:
```bash
make rollback
```
This runs `scripts/deployment/rollback.sh list` to display all git rollback safety tags and local snapshots.
To apply a rollback, execute:
```bash
./scripts/deployment/rollback.sh apply <tag_or_patch_file>
```
This safely reverts files while capturing a safety backup of your current state.

---

## 📊 SonarQube Quality Gate

**IA-Framework** features a robust out-of-the-box **SonarQube Quality Gate** integration to measure bugs, code smells, vulnerabilities, security hotspots, and unit test coverage in both local and remote environments.

### 🛡️ Remote Quality Gate (CI)
On Pull Request creation, the CI action `.github/workflows/ci-quality-gate.yml` will automatically trigger a SonarQube Scanner scan. It enforces remote verification of the Quality Gate, blocking PR merges if the status is red (using secret values `SONAR_HOST_URL` and `SONAR_TOKEN`).

### 💻 Local Quality Gate (Developer Sandbox)
You do not need to wait for remote CI/CD pipelines to know if your changes will pass the SonarQube Quality Gate. Run the local gate command:
```bash
make sonar-check
```
This command runs:
1.  **Test Coverage Collection:** Executes tests generating `coverage.xml`.
2.  **Local Sonar Scan:** Triggers a Dockerized `sonar-scanner-cli` to analyze source files and publish metrics locally or to a shared SonarQube server.
3.  **Project Status API Poll:** Queries the SonarQube project status API to check if it's `OK` or `ERROR`.
4.  **Error Diagnostics:** Prints a colorized report displaying failed conditions, code issues, severity, and files with uncovered code.

To customize Sonar scanner properties (e.g. project name, file inclusions/exclusions, source path), edit `sonar-project.properties` in your repository root.

---

## 📄 License

This framework is open-source software licensed under the [MIT License](LICENSE).
