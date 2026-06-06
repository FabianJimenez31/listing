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
echo -e "${YELLOW}🚀 Running pre-push checks...${NC}"
ERRORS=0
current_branch=$(git rev-parse --abbrev-ref HEAD)

# 1. Block direct push to protected branches
case "$current_branch" in
    main|master|prod|staging|develop)
        echo -e "${RED}   ❌ Direct push to '$current_branch' is blocked! Use Pull Requests to merge code.${NC}"
        ERRORS=$((ERRORS + 1))
        ;;
esac

# 2. Check for large files
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
if grep -q "^test:" Makefile 2>/dev/null; then
    echo -e "${BLUE}   Running automated test suite (make test)...${NC}"
    if make test > /tmp/harness_tests.log 2>&1; then
        echo -e "${GREEN}   ✅ Test suite PASSED successfully!${NC}"
    else
        echo -e "${RED}   ❌ Test suite FAILED. See /tmp/harness_tests.log for details:${NC}"
        tail -n 20 /tmp/harness_tests.log
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${YELLOW}   ⚠️  No test suite found in Makefile. Skipping tests check.${NC}"
fi

if [ "$ERRORS" -gt 0 ]; then
    echo -e "${RED}❌ pre-push Gate FAILED. Push aborted.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ pre-push Gate PASSED. Initiating push...${NC}"
exit 0
