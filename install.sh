#!/usr/bin/env bash
# IA-Framework: Turnkey Quality Gate and Spec-Kit Installer Script

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================================================"${NC}
echo -e "${BLUE}⚡ IA-Framework Quality Gate & Spec-Kit Installer ⚡"${NC}
echo -e "${BLUE}======================================================================"${NC}
echo ""

# 1. Verify Git Repository
if ! command -v git >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] git command not found. Please install git before proceeding.${NC}"
    exit 1
fi

if [ ! -d ".git" ]; then
    echo -e "${YELLOW}[WARNING] No .git folder detected in the current directory.${NC}"
    read -rp "Do you want to initialize a new Git repository here? [y/N]: " GIT_INIT
    if [[ "$GIT_INIT" =~ ^[Yy] ]]; then
        git init
        echo -e "${GREEN}[SUCCESS] Git repository initialized!${NC}"
    else
        echo -e "${RED}[ERROR] Installation aborted. Git is required to set up hooks.${NC}"
        exit 1
    fi
fi

# 2. Make directories
echo -e "${BLUE}[INFO] Setting up directory structures...${NC}"
mkdir -p specs
mkdir -p temp/debug temp/patches temp/testing temp/backup temp/emergency_logs
mkdir -p src tests
mkdir -p scripts/validation scripts/harness scripts/deployment

# 3. Configure file permissions
echo -e "${BLUE}[INFO] Configuring execute permissions for scripts...${NC}"
find .specify/scripts/bash/ -type f -name "*.sh" -exec chmod +x {} \; || true
find .claude/hooks/ -type f -name "*.sh" -exec chmod +x {} \; || true
find scripts/ -type f -name "*.sh" -exec chmod +x {} \; || true
find scripts/ -type f -name "*.py" -exec chmod +x {} \; || true
chmod +x .claude/hooks/git/pre-commit || true
chmod +x .claude/hooks/git/pre-push || true
chmod +x sonar_local.sh || true

# 4. Install Git Hooks
echo -e "${BLUE}[INFO] Binding Git Hooks using core.hooksPath...${NC}"
git config core.hooksPath .claude/hooks/git
echo -e "${GREEN}[SUCCESS] Git hooks successfully linked to .claude/hooks/git!${NC}"

# 5. Setup Boilerplate CLAUDE.md / AGENTS.md
if [ ! -f "CLAUDE.md" ]; then
    echo -e "${BLUE}[INFO] Creating boilerplate CLAUDE.md project constitution...${NC}"
    if [ -f ".specify/templates/constitution-template.md" ]; then
        cp ".specify/templates/constitution-template.md" "CLAUDE.md"
        echo -e "${GREEN}[SUCCESS] CLAUDE.md created!${NC}"
    fi
fi

if [ ! -f "AGENTS.md" ]; then
    echo -e "${BLUE}[INFO] Creating boilerplate AGENTS.md mirror...${NC}"
    if [ -f "CLAUDE.md" ]; then
        cp "CLAUDE.md" "AGENTS.md"
        echo -e "${GREEN}[SUCCESS] AGENTS.md created!${NC}"
    fi
fi

# 6. Add standard ignore patterns to .gitignore
echo -e "${BLUE}[INFO] Verifying .gitignore rules...${NC}"
touch .gitignore
patterns=("temp/debug/" "temp/patches/" "temp/testing/" "*.log" "__pycache__/" "node_modules/")
for p in "${patterns[@]}"; do
    if ! grep -qxF "$p" .gitignore; then
        echo "$p" >> .gitignore
    fi
done

echo ""
echo -e "${GREEN}======================================================================"${NC}
echo -e "${GREEN}🎉 IA-Framework Installation Complete! 🎉"${NC}
echo -e "${GREEN}======================================================================"${NC}
echo ""
echo -e "You can now use the following commands:"
echo -e "  - ${YELLOW}make spec-new${NC}  : Interactively create a feature branch & spec files"
echo -e "  - ${YELLOW}make dev-check${NC} : Run local validation checks before committing"
echo -e "  - ${YELLOW}make test${NC}      : Run automated tests"
echo ""
echo -e "Enforce strict AI safeguards, Git Flow branching, and specifications!"
echo -e "${GREEN}Let's build with quality! 🚀${NC}"
echo ""
exit 0
