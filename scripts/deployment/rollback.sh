#!/usr/bin/env bash
# Standardized Local & Git Rollback Executor
#
# Atomic rollback script to revert broken deployments or hotfixes.
# Restores working workspaces from tags, commits, or safety patch snapshots.
#
# Usage:
#   ./rollback.sh list            : List all available tags and local patches
#   ./rollback.sh apply <target>  : Revert workspace to the specified target

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ACTION="${1:-}"
TARGET="${2:-}"

show_help() {
    echo "Usage: $0 {list|apply <target>}"
    echo "   list  - Lists available git rollback tags and patch snapshots"
    echo "   apply - Restores the workspace to a specified tag or patch"
}

if [[ -z "$ACTION" ]]; then
    show_help
    exit 1
fi

case "$ACTION" in
    list)
        echo -e "${BLUE}======================================================================${NC}"
        echo -e "⏪ AVAILABLE ROLLBACK AND RESTORE TARGETS ⏪"
        echo -e "${BLUE}======================================================================${NC}\n"
        
        echo -e "${YELLOW}[Git Emergency & Deploy Rollback Tags]${NC}"
        # Lists git tags containing 'rollback' or 'emergency'
        git tag -l "*rollback*" "*emergency*" 2>/dev/null | sed 's/^/  - /' || echo "  No git rollback tags found."
        
        echo -e "\n${YELLOW}[Workspace Safety Patch Snapshots]${NC}"
        # Lists files in temp/backup
        if [ -d "temp/backup" ]; then
            find temp/backup/ -type f -name "emergency_snapshot_*.patch" 2>/dev/null | sed 's/^/  - /' || echo "  No local patch snapshots found."
        else
            echo "  No local backup directory found."
        fi
        
        echo -e "\n💡 To perform a rollback, run: ${YELLOW}./rollback.sh apply <target_name>${NC}"
        ;;
        
    apply)
        if [[ -z "$TARGET" ]]; then
            echo -e "${RED}[ERROR] Please specify a rollback target (git tag, commit hash, or patch file path).${NC}" >&2
            exit 1
        fi
        
        echo -e "${RED}⚠️  INITIATING ATOMIC WORKSPACE ROLLBACK TO: ${YELLOW}${TARGET}${NC}..."
        
        # 1. Backup dirty changes before checkout/rollback (never lose code!)
        SNAPSHOT_PATCH="temp/backup/pre_rollback_safety_$(date +%Y%m%d_%H%M%S).patch"
        echo -e "${BLUE}[INFO] Stashing current uncommitted changes to ${SNAPSHOT_PATCH}...${NC}"
        git diff > "$SNAPSHOT_PATCH" || true
        
        # 2. Check if the target is a local patch file
        if [[ -f "$TARGET" ]]; then
            echo -e "${BLUE}[INFO] Applying local patch file: ${TARGET}...${NC}"
            git checkout .
            git clean -fd
            if git apply "$TARGET"; then
                echo -e "${GREEN}✅ Rollback patch applied successfully!${NC}"
                exit 0
            else
                echo -e "${RED}❌ FAILED to apply rollback patch! Reverting patch state.${NC}" >&2
                git checkout .
                exit 1
            fi
        fi
        
        # 3. Check if target is a Git tag/commit
        if git rev-parse "$TARGET" >/dev/null 2>&1; then
            echo -e "${BLUE}[INFO] Performing Git checkout of target: ${TARGET}...${NC}"
            git checkout "$TARGET"
            echo -e "${GREEN}✅ Git workspace successfully reverted to ${TARGET}!${NC}"
            echo -e "${YELLOW}💡 Warning: You are in a 'detached HEAD' state. Create a branch to make new commits.${NC}"
            exit 0
        fi
        
        echo -e "${RED}❌ Target '${TARGET}' was not recognized as a valid Git entity or patch file!${NC}" >&2
        exit 1
        ;;
        
    *)
        show_help
        exit 1
        ;;
esac
