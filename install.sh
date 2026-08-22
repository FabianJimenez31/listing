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

# 5. Install and configure Engram (persistent memory)
echo -e "${BLUE}[INFO] Setting up persistent memory (Engram)...${NC}"

for tool in curl jq; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo -e "${RED}[ERROR] '$tool' is required by the harness but was not found.${NC}"
        echo -e "${YELLOW}        Install it and re-run ./install.sh${NC}"
        exit 1
    fi
done

if ! command -v engram >/dev/null 2>&1; then
    echo -e "${YELLOW}[WARNING] Engram is not installed. Memory is a required part of this framework.${NC}"
    if command -v brew >/dev/null 2>&1; then
        read -rp "Install Engram now via Homebrew? [Y/n]: " INSTALL_ENGRAM
        if [[ ! "$INSTALL_ENGRAM" =~ ^[Nn] ]]; then
            brew install gentleman-programming/tap/engram || true
        fi
    else
        echo -e "${YELLOW}        Homebrew not found. Install Engram manually:${NC}"
        echo -e "${YELLOW}        https://github.com/Gentleman-Programming/engram#install${NC}"
    fi
fi

if ! command -v engram >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] Engram is still unavailable. The memory gate cannot run without it.${NC}"
    echo -e "${RED}        Installation aborted. Install Engram and re-run ./install.sh${NC}"
    exit 1
fi
echo -e "${GREEN}[SUCCESS] Engram found: $(command -v engram)${NC}"

# Pin the project name. Engram otherwise resolves it from cwd through six
# fallback levels, which lets two machines write to different buckets for the
# same repository. A versioned .engram/config.json has the highest precedence.
mkdir -p .engram
if [ ! -f ".engram/config.json" ]; then
    PROJECT_NAME="$(basename "$(pwd)")"
    printf '{\n  "project_name": "%s"\n}\n' "$PROJECT_NAME" > .engram/config.json
    echo -e "${GREEN}[SUCCESS] Project pinned as '${PROJECT_NAME}' in .engram/config.json${NC}"
fi

# Register Engram with the coding agents this project supports.
echo -e "${BLUE}[INFO] Which agents should be configured for memory?${NC}"
echo -e "   1) Claude Code    2) Codex    3) Kiro    4) All    5) Skip"
read -rp "Select [4]: " AGENT_CHOICE
AGENT_CHOICE="${AGENT_CHOICE:-4}"
setup_agent() {
    echo -e "${BLUE}[INFO] Configuring $1...${NC}"
    engram setup "$1" >/dev/null 2>&1 \
        && echo -e "${GREEN}[SUCCESS] $1 configured.${NC}" \
        || echo -e "${YELLOW}[WARNING] 'engram setup $1' failed; configure it manually.${NC}"
}
case "$AGENT_CHOICE" in
    1) setup_agent claude-code ;;
    2) setup_agent codex ;;
    3) setup_agent kiro ;;
    4) setup_agent claude-code; setup_agent codex; setup_agent kiro ;;
    *) echo -e "${YELLOW}[INFO] Skipped agent configuration.${NC}" ;;
esac

# Start the daemon. The harness writes memory over HTTP, not MCP, so the daemon
# must be reachable for the git hooks to record anything.
if ! curl -sf --max-time 2 "http://127.0.0.1:${ENGRAM_PORT:-7437}/health" >/dev/null 2>&1; then
    echo -e "${BLUE}[INFO] Starting the Engram daemon...${NC}"
    ( engram serve >/dev/null 2>&1 & ) >/dev/null 2>&1
    sleep 2
fi
if curl -sf --max-time 2 "http://127.0.0.1:${ENGRAM_PORT:-7437}/health" >/dev/null 2>&1; then
    echo -e "${GREEN}[SUCCESS] Engram daemon is reachable.${NC}"
    # Seed the personal-scope preferences state so the memory gate has something
    # to verify from the first task instead of blocking on a bootstrap gap.
    if [ -x "scripts/memory/capture_stage.sh" ]; then
        bash scripts/memory/capture_stage.sh preferences \
            "Follow the IA-Framework constitution in CLAUDE.md and AGENTS.md." >/dev/null 2>&1 || true
    fi
else
    echo -e "${YELLOW}[WARNING] Daemon not reachable. Start it with: engram serve${NC}"
fi

# 6. Setup Boilerplate CLAUDE.md / AGENTS.md
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

# 7. Add standard ignore patterns to .gitignore
echo -e "${BLUE}[INFO] Verifying .gitignore rules...${NC}"
touch .gitignore
patterns=("temp/debug/" "temp/patches/" "temp/testing/" "temp/logs/" "temp/.harness_emergency" "*.log" "__pycache__/" "node_modules/")
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
echo -e "  - ${YELLOW}make mem-context${NC} : Show what the project already remembers"
echo -e "  - ${YELLOW}make mem-check${NC}   : Verify the memory quota for this branch"
echo ""
echo -e "Enforce strict AI safeguards, Git Flow branching, and specifications!"
echo -e "${GREEN}Let's build with quality! 🚀${NC}"
echo ""
exit 0
