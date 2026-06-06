# Makefile for IA-Framework Quality Gate Harness

.PHONY: init-harness dev-check spec-new test clean sonar-check lint-nginx smoke-test validate-enums hotfix rollback help

help:
	@echo "======================================================================"
	@echo "IA-Framework Developer CLI Commands:"
	@echo "======================================================================"
	@echo "  make init-harness   - Install Git hooks and initialize directory structure"
	@echo "  make dev-check      - Run local pre-commit checks (simulate Git hooks)"
	@echo "  make spec-new       - Interactively create a new spec-driven feature branch"
	@echo "  make test           - Execute automated test suite"
	@echo "  make lint-nginx     - [NEW] Validate Nginx upstream patterns for IPv6 hazards"
	@echo "  make smoke-test     - [NEW] Run SPA deployment atomicity smoke tests"
	@echo "  make validate-enums - [NEW] Run code enums vs database values validator"
	@echo "  make hotfix         - [NEW] Declare and organize structured emergency hotfix"
	@echo "  make rollback       - [NEW] List rollback safe points or revert changes"
	@echo "  make sonar-check    - Execute local SonarQube scanner & Quality Gate check"
	@echo "  make clean          - Run smart cleanup of temporary log and backup files"
	@echo "======================================================================"

init-harness:
	@chmod +x install.sh
	@./install.sh

dev-check:
	@chmod +x .claude/hooks/pre-commit.sh
	@bash .claude/hooks/pre-commit.sh

spec-new:
	@chmod +x .specify/scripts/bash/create-new-feature.sh
	@bash .specify/scripts/bash/create-new-feature.sh

test:
	@if command -v pytest >/dev/null 2>&1; then \
		pytest tests/ -v; \
	else \
		echo "pytest not installed. Create a virtual environment and run 'pip install pytest'."; \
	fi

lint-nginx:
	@chmod +x scripts/harness/lint_nginx.sh
	@bash scripts/harness/lint_nginx.sh

smoke-test:
	@chmod +x scripts/harness/smoke_test_frontend.sh
	@bash scripts/harness/smoke_test_frontend.sh

validate-enums:
	@python3 scripts/validation/validate_enums.py

hotfix:
	@chmod +x scripts/deployment/emergency_hotfix.sh
	@bash scripts/deployment/emergency_hotfix.sh crear

rollback:
	@chmod +x scripts/deployment/rollback.sh
	@bash scripts/deployment/rollback.sh list

sonar-check:
	@chmod +x sonar_local.sh
	@bash sonar_local.sh

clean:
	@chmod +x .claude/hooks/smart-cleanup.sh
	@bash .claude/hooks/smart-cleanup.sh

