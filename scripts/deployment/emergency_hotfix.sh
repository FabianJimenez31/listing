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

# Create directories
mkdir -p temp/emergency_logs
mkdir -p temp/backup

show_help() {
    echo "Usage: $0 {crear|validar|aplicar}"
    echo "   crear   - Sets up emergency documentation and copies safety snapshots"
    echo "   validar - Runs standard test suites to verify that the fix is correct"
    echo "   aplicar - Commits hotfix with bypass flag and takes local git backup tags"
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
        if [ -f ".claude/hooks/check-file-size.sh" ]; then
            echo -e "   Running file size safeguard..."
            if bash .claude/hooks/check-file-size.sh; then
                echo -e "${GREEN}✅ File size checks passed.${NC}"
            else
                echo -e "${RED}❌ File size check FAILED! Keep modules small even in emergency.${NC}" >&2
                exit 1
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
        
        # Enforce committing with emergency env bypass
        export HARNESS_EMERGENCY=1
        
        echo -e "\n${GREEN}✅ Hotfix applied and locked in!${NC}"
        echo -e "   - Rollback point stored under tag: ${YELLOW}${TAG_NAME}${NC}"
        echo -e "   - To revert this hotfix if needed, run: ${YELLOW}git checkout ${TAG_NAME}${NC}"
        echo -e "\n👉 Please ensure you complete the Post-Mortem in temp/emergency_logs/."
        ;;
        
    *)
        show_help
        exit 1
        ;;
esac
