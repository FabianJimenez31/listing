# Makefile for IA-Framework Quality Gate Harness

# Stage evaluated by 'make mem-check'. Override with: make mem-check STAGE=merge
STAGE ?= push

.PHONY: init-harness dev-check spec-new test clean sonar-check sonar-up sonar-down lint-nginx smoke-test validate-enums hotfix emergency-clear rollback mem-context mem-check mem-capture mem-doctor mem-ingest help

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
	@echo "  make emergency-clear- [NEW] Clear the emergency bypass and re-arm all gates"
	@echo "  make rollback       - [NEW] List rollback safe points or revert changes"
	@echo "  make mem-context    - [NEW] Show what the project already remembers"
	@echo "  make mem-check      - [NEW] Verify the memory quota for the current branch"
	@echo "  make mem-capture    - [NEW] Capture the memory states derivable right now"
	@echo "  make mem-doctor     - [NEW] Diagnose the Engram memory subsystem"
	@echo "  make mem-ingest     - [NEW] Ingest a CI outcome artifact into local memory"
	@echo "  make sonar-up       - Start local Dockerized SonarQube + write token to .env.local"
	@echo "  make sonar-down     - Stop and remove the local SonarQube container"
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

emergency-clear:
	@chmod +x scripts/deployment/emergency_hotfix.sh
	@bash scripts/deployment/emergency_hotfix.sh limpiar

mem-context:
	@bash -c 'source scripts/memory/engram_client.sh && mem_ensure_daemon && mem_context | jq .'

mem-check:
	@bash scripts/memory/memory_gate.sh $(STAGE)

mem-capture:
	@bash scripts/memory/capture_stage.sh session-open >/dev/null
	@bash scripts/memory/capture_stage.sh semantic   || true
	@bash scripts/memory/capture_stage.sh procedural || true
	@bash scripts/memory/capture_stage.sh decision   || true
	@echo "Captured every memory state derivable from the current working tree."

mem-doctor:
	@bash -c 'source scripts/memory/engram_client.sh && mem_ensure_daemon && mem_doctor | jq .'

mem-ingest:
	@bash scripts/memory/ingest_ci_outcome.sh $(ARTIFACT)

rollback:
	@chmod +x scripts/deployment/rollback.sh
	@bash scripts/deployment/rollback.sh list

sonar-up:
	@chmod +x scripts/harness/sonar_server.sh
	@bash scripts/harness/sonar_server.sh up

sonar-down:
	@chmod +x scripts/harness/sonar_server.sh
	@bash scripts/harness/sonar_server.sh down

sonar-check:
	@chmod +x sonar_local.sh
	@bash sonar_local.sh

clean:
	@chmod +x .claude/hooks/smart-cleanup.sh
	@bash .claude/hooks/smart-cleanup.sh

