#!/bin/bash
# Git pre-push hook. Validates code sanity and pushes local testing gates before remote push.

set -e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

cd "$PROJECT_DIR"

if [ -f ".claude/hooks/emergency_state.sh" ]; then
    # shellcheck source=/dev/null
    source ".claude/hooks/emergency_state.sh"
fi

EMERGENCY=0
if command -v harness_emergency_active >/dev/null 2>&1 && harness_emergency_active; then
    EMERGENCY=1
fi

echo -e "${YELLOW}🚀 Running pre-push checks...${NC}"
if [ "$EMERGENCY" -eq 1 ]; then
    harness_emergency_notice "protected-branch block and test suite"
fi
ERRORS=0
current_branch=$(git rev-parse --abbrev-ref HEAD)

# 1. Block direct push to protected branches
if [ "$EMERGENCY" -eq 0 ]; then
    case "$current_branch" in
        main|master|prod|staging|develop)
            echo -e "${RED}   ❌ Direct push to '$current_branch' is blocked! Use Pull Requests to merge code.${NC}"
            ERRORS=$((ERRORS + 1))
            ;;
    esac
fi

# 2. Check for large files
#    Safety gate: enforced even under an emergency bypass.
large_files=""
while read -r f; do
    if [ -n "$f" ] && [ -f "$f" ]; then
        size=$(wc -c < "$f" 2>/dev/null || echo 0)
        # Block files > 10MB
        if [ "$size" -gt 10485760 ]; then
            echo -e "${RED}   ❌ BLOCK: File '$f' is larger than 10MB ($((size / 1048576)) MB). Large files are blocked.${NC}"
            ERRORS=$((ERRORS + 1))
        # Warn files > 1MB
        elif [ "$size" -gt 1048576 ]; then
            large_files+="$f ($((size / 1048576)) MB)"$'\n'
        fi
    fi
done < <(git diff --name-only "@{u}..HEAD" 2>/dev/null || true)

if [ -n "$large_files" ]; then
    echo -e "${YELLOW}   ⚠️  Warning: Large files (>1MB) detected in this push:${NC}"
    echo "$large_files" | sed 's/^/      /'
fi

# 3. Run automated tests if available
if [ "$EMERGENCY" -eq 1 ]; then
    echo -e "${YELLOW}   ⏭️  Test suite skipped by emergency bypass."
    echo -e "      Run 'make hotfix' -> 'validar' to verify the fix.${NC}"
    TEST_OUTCOME="skipped"
elif grep -q "^test:" Makefile 2>/dev/null; then
    echo -e "${BLUE}   Running automated test suite (make test)...${NC}"
    mkdir -p temp/logs
    if make test > temp/logs/harness_tests.log 2>&1; then
        echo -e "${GREEN}   ✅ Test suite PASSED successfully!${NC}"
        TEST_OUTCOME="passed"
    else
        echo -e "${RED}   ❌ Test suite FAILED. See temp/logs/harness_tests.log for details:${NC}"
        tail -n 20 temp/logs/harness_tests.log
        TEST_OUTCOME="failed"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${YELLOW}   ⚠️  No test suite found in Makefile. Skipping tests check.${NC}"
    TEST_OUTCOME="unknown"
fi

# 4. Record the outcome, then verify the memory quota.
#    Capture runs before the gate so the state it produces is visible to it.
if [ -x "scripts/memory/capture_stage.sh" ]; then
    bash scripts/memory/capture_stage.sh outcome "${TEST_OUTCOME:-unknown}" \
         "temp/logs/harness_tests.log" >/dev/null 2>&1 || true
fi

if [ -x "scripts/memory/memory_gate.sh" ]; then
    if ! bash scripts/memory/memory_gate.sh push; then
        ERRORS=$((ERRORS + 1))
    fi
fi

if [ "$ERRORS" -gt 0 ]; then
    echo -e "${RED}❌ pre-push Gate FAILED. Push aborted.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ pre-push Gate PASSED. Initiating push...${NC}"
exit 0
