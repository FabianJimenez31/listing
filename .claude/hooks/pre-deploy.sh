#!/bin/bash
# Pre-deploy checklist to ensure quality before deployment.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}📦 Running Pre-deployment Checks...${NC}"
ERRORS=0

# Ensure we are not on a feature branch (deploys should only happen on protected/release branches)
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [[ "$current_branch" =~ ^feature/ ]]; then
    echo -e "${RED}   ❌ BLOCK: Cannot deploy directly from a feature branch '$current_branch'. Please merge into main first.${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Run pre-commit to check code boundaries
if [ -f ".claude/hooks/pre-commit.sh" ]; then
    if ! bash .claude/hooks/pre-commit.sh; then
        echo -e "${RED}   ❌ BLOCK: Local quality checks failed.${NC}"
        ERRORS=$((ERRORS + 1))
    fi
fi

if [ "$ERRORS" -gt 0 ]; then
    echo -e "${RED}❌ Pre-deployment quality checks FAILED ($ERRORS errors). Deployment aborted.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Pre-deployment checks PASSED. Ready to deploy!${NC}"
exit 0
