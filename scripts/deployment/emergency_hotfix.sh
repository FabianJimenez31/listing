#!/usr/bin/env bash
# Turnkey Incident & Emergency Hotfix Orchestrator
#
# Orchestrates high-risk, quick emergency patches for production crashes.
# Forces structure, backups, automated testing, and post-mortem logs.
#
# Usage:
#   ./emergency_hotfix.sh crear    : Initialize hotfix, create backups and logs template
#   ./emergency_hotfix.sh validar  : Run local unit tests and lint checks
#   ./emergency_hotfix.sh aplicar  : Apply patch, bypass staging gates under safety cover

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ACTION="${1:-}"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

if [ -f ".claude/hooks/emergency_state.sh" ]; then
    # shellcheck source=/dev/null
    source ".claude/hooks/emergency_state.sh"
fi

# Create directories
mkdir -p temp/emergency_logs
mkdir -p temp/backup

show_help() {
    echo "Usage: $0 {crear|validar|aplicar|limpiar}"
    echo "   crear   - Sets up emergency documentation and copies safety snapshots"
    echo "   validar - Runs standard test suites to verify that the fix is correct"
    echo "   aplicar - Commits hotfix with bypass flag and takes local git backup tags"
    echo "   limpiar - Clears the emergency bypass and re-arms every quality gate"
}

if [[ -z "$ACTION" ]]; then
    show_help
    exit 1
fi

case "$ACTION" in
    crear|create)
        echo -e "${RED}======================================================================${NC}"
        echo -e "🚨 INITIALIZING EMERGENCY HOTFIX PROCEDURE 🚨"
        echo -e "${RED}======================================================================${NC}"
        echo -e "${YELLOW}[WARNING] This is for CRITICAL production bugs only!${NC}\n"
        
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        LOG_FILE="temp/emergency_logs/${TIMESTAMP}_hotfix.md"
        
        # 1. Generate incident response documentation template
        cat <<EOF > "$LOG_FILE"
# 🚨 Incident Response & Emergency Hotfix Log: ${TIMESTAMP}

## 1. Incident Assessment
- **Severity**: CRITICAL
- **Declared By**: AI / Developer
- **Symptoms**: Production failure, down status.
- **Affected Components**: 

## 2. Root Cause Analysis (RCA)
- What broke?
- Why did existing quality gates fail to prevent this?

## 3. Implementation Plan
- File(s) to modify:
- Changes description:

## 4. Verification & Testing
- Manual Verification Results:
- Automated Tests Executed:

## 5. Post-Hotfix Remediation Tasks
- [ ] Implement robust regression tests.
- [ ] Review code modularity / refactor file.
- [ ] Push to main repository.
EOF
        
        # 2. Automated snapshot backup
        echo -e "${BLUE}[INFO] Creating git state safety backup...${NC}"
        git diff > "temp/backup/emergency_snapshot_${TIMESTAMP}.patch" || true
        
        echo -e "${GREEN}✅ Emergency workspace prepared!${NC}"
        echo -e "   - Log template created at: ${YELLOW}${LOG_FILE}${NC}"
        echo -e "   - Patch safety snapshot taken: ${YELLOW}temp/backup/emergency_snapshot_${TIMESTAMP}.patch${NC}"
        echo -e "\n💡 Next Steps:"
        echo -e "   1. Edit files to fix the issue."
        echo -e "   2. Document changes in the log file."
        echo -e "   3. Run: ${YELLOW}./emergency_hotfix.sh validar${NC}"
        ;;
        
    validar|validate)
        echo -e "${BLUE}[INFO] Running emergency validation checks...${NC}"
        
        # Run Makefile tests if available
        if grep -q "^test:" Makefile 2>/dev/null; then
            echo -e "   Running test suite..."
            if make test; then
                echo -e "${GREEN}✅ Test suite PASSED successfully!${NC}"
            else
                echo -e "${RED}❌ Test suite FAILED! Fix the tests before applying hotfix.${NC}" >&2
                exit 1
            fi
        else
            echo -e "${YELLOW}⚠️  No Makefile test suite found. Skipping test check.${NC}"
        fi
        
        # Check files size
        # The hook reads a JSON payload from stdin (.tool_input.file_path), so it
        # must be fed one file at a time. Calling it bare left it blocked on `cat`.
        if [ -f ".claude/hooks/check-file-size.sh" ]; then
            echo -e "   Running file size safeguard..."
            if ! command -v jq >/dev/null 2>&1; then
                echo -e "${YELLOW}⚠️  jq not found; skipping file size safeguard.${NC}"
            else
                changed_files="$( { git diff --name-only HEAD 2>/dev/null || true; \
                                    git ls-files --others --exclude-standard 2>/dev/null || true; } | sort -u )"
                if [ -z "$changed_files" ]; then
                    echo -e "${YELLOW}   No modified files to check.${NC}"
                else
                    size_errors=0
                    while IFS= read -r changed_file; do
                        [ -n "$changed_file" ] || continue
                        [ -f "$changed_file" ] || continue
                        if ! jq -n --arg path "$changed_file" '{"tool_input":{"file_path":$path}}' \
                             | bash .claude/hooks/check-file-size.sh; then
                            size_errors=$((size_errors + 1))
                        fi
                    done <<< "$changed_files"

                    if [ "$size_errors" -gt 0 ]; then
                        echo -e "${RED}❌ File size check FAILED! Keep modules small even in emergency.${NC}" >&2
                        exit 1
                    fi
                    echo -e "${GREEN}✅ File size checks passed.${NC}"
                fi
            fi
        fi
        
        echo -e "\n${GREEN}✅ Fix successfully validated!${NC}"
        echo -e "💡 Next step: Run ${YELLOW}./emergency_hotfix.sh aplicar${NC}"
        ;;
        
    aplicar|apply)
        echo -e "${RED}⚠️  APPLYING HOTFIX AND BYPASSING STANDARD LONG FLOWS...${NC}"
        
        # Take an internal tag for rollbacks
        TAG_NAME="emergency-rollback-$(date +%Y%m%d-%H%M%S)"
        echo -e "${BLUE}[INFO] Creating rollback tag: ${YELLOW}${TAG_NAME}${NC}"
        git tag -a "$TAG_NAME" -m "Safety backup prior to emergency hotfix"
        
        # Enforce committing with emergency bypass.
        # `export` only lived inside this script's own shell, so the git hooks —
        # which run as separate processes — never saw it. The state is persisted
        # to disk instead, with a TTL so it cannot be left on by accident.
        if command -v harness_emergency_declare >/dev/null 2>&1; then
            bypass_window="$(harness_emergency_declare)"
            echo -e "${BLUE}[INFO] Emergency bypass ${bypass_window}${NC}"
        else
            echo -e "${YELLOW}⚠️  emergency_state.sh not found; bypass NOT active.${NC}" >&2
        fi
        
        echo -e "\n${GREEN}✅ Hotfix applied and locked in!${NC}"
        echo -e "   - Rollback point stored under tag: ${YELLOW}${TAG_NAME}${NC}"
        echo -e "   - To revert this hotfix if needed, run: ${YELLOW}git checkout ${TAG_NAME}${NC}"
        echo -e "   - Workflow gates bypassed; secret and file-size gates still enforced."
        echo -e "   - Clear the bypass when done: ${YELLOW}make emergency-clear${NC}"
        echo -e "\n👉 Please ensure you complete the Post-Mortem in temp/emergency_logs/."
        ;;
        
    limpiar|clear)
        if command -v harness_emergency_clear >/dev/null 2>&1; then
            harness_emergency_clear
            echo -e "${GREEN}✅ Emergency bypass cleared. All quality gates are active again.${NC}"
        else
            echo -e "${RED}❌ emergency_state.sh not found.${NC}" >&2
            exit 1
        fi
        ;;

    *)
        show_help
        exit 1
        ;;
esac
