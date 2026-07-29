# Listing — IA-Framework Harness Setup

This project is bootstrapped with the **IA-Framework** quality-gate + spec-kit
harness, adapted for a **Python** codebase with a **local Dockerized SonarQube**.

## What's configured

| Area | Status |
|------|--------|
| Git hooks (`core.hooksPath=.claude/hooks/git`) | ✅ pre-commit / pre-push active |
| Spec-driven workflow (`make spec-new`) | ✅ (sed range bug fixed) |
| File-size gate (1000 hard / 800 warn) | ✅ |
| Architecture validator | ✅ `scripts/validation/validate_structure.py` |
| Enum validator | ⏸️ disabled until DB schema is defined |
| Tests + coverage | ✅ pytest + pytest-cov (`coverage.xml`) |
| SonarQube (local, Docker) | ✅ `lts-community` on :9000, Quality Gate green |
| GitHub Actions CI | ✅ `.github/workflows/` (needs repo secrets) |

## Prerequisites installed

- Python deps: `pip install -r requirements-dev.txt`
- Docker (daemon running) — for the SonarQube scanner + local server

## SonarQube — local server

```bash
make sonar-up      # start container, wait, write SONAR_TOKEN to .env.local
make sonar-check   # run tests+coverage, scan, poll Quality Gate
make sonar-down    # stop & remove container
```

- Server: http://localhost:9000  (admin / `Sonar_Listing_2026!`)
- Dashboard: http://localhost:9000/dashboard?id=listing
- Credentials live in `.env.local` (git-ignored). Never commit it.

## Daily workflow

```bash
make spec-new                 # create feature/NNN-slug branch + spec/plan/tasks
# ... edit specs, write code in src/, tests in tests/ ...
make dev-check                # local gate (branch, specs, secrets, structure, size)
make test                     # pytest
make sonar-check              # local Quality Gate (optional, needs sonar-up)
git commit                    # real git hook re-runs the gate
git push                      # opens PR -> CI runs the remote Quality Gate
```

## CI secrets (GitHub)

For the remote SonarQube gate in `.github/workflows/ci-quality-gate.yml`, set:

- `SONAR_HOST_URL`
- `SONAR_TOKEN`

(A localhost server is not reachable from GitHub-hosted runners — point these at
a hosted SonarQube / SonarCloud instance for CI.)

## Adaptations applied to the upstream framework

- `sonar-project.properties`: `projectKey/Name = listing`, `sonar.python.version=3.13`.
- `pre-commit.sh` + `.pre-commit-config.yaml`: added `sonar_local.sh` to the
  root-script allowlist (framework shipped it in root but blocked it).
- `create-new-feature.sh`: fixed invalid `sed` character range that aborted the script.
- `validate_enums.py`: kept generic; enum gate disabled in pre-commit until the DB is defined.
- Added `scripts/harness/sonar_server.sh` + `make sonar-up`/`sonar-down`.
- Added `requirements.txt`, `requirements-dev.txt`, `.env.example`, sample
  `src/listing_catalog.py` + tests.
