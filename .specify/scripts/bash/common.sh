#!/usr/bin/env bash
# Common functions and variables for IA-Framework Spec-Kit

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Find the repository root by searching upward for the .specify directory
find_specify_root() {
    local dir="${1:-$(pwd)}"
    dir="$(cd -- "$dir" 2>/dev/null && pwd)" || return 1
    local prev_dir=""
    while true; do
        if [ -d "$dir/.specify" ]; then
            echo "$dir"
            return 0
        fi
        if [ "$dir" = "/" ] || [ "$dir" = "$prev_dir" ]; then
            break
        fi
        prev_dir="$dir"
        dir="$(dirname "$dir")"
    done
    return 1
}

# Resolve the project root
get_repo_root() {
    local specify_root
    if specify_root=$(find_specify_root); then
        echo "$specify_root"
        return
    fi
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
        return
    fi
    pwd
}

# Check if git is available and initialized
has_git() {
    command -v git >/dev/null 2>&1 || return 1
    local repo_root
    repo_root=$(get_repo_root)
    [ -d "$repo_root/.git" ] || [ -f "$repo_root/.git" ] || return 1
    git -C "$repo_root" rev-parse --is-inside-work-tree >/dev/null 2>&1
}

# Resolve effective branch name (strip prefix segment like feature/001-login -> 001-login)
spec_kit_effective_branch_name() {
    local raw="$1"
    if [[ "$raw" =~ ^([^/]+)/([^/]+)$ ]]; then
        printf '%s\n' "${BASH_REMATCH[2]}"
    else
        printf '%s\n' "$raw"
    fi
}

# Verify feature branch naming conventions
check_feature_branch() {
    local branch_name="$1"
    local has_git_repo="$2"

    if [[ "$has_git_repo" != "true" ]]; then
        return 0
    fi

    # Feature branch naming convention: e.g. feature/001-login
    if [[ "$branch_name" =~ ^feature/ ]]; then
        local slug
        slug=$(spec_kit_effective_branch_name "$branch_name")
        if [[ ! "$slug" =~ ^[0-9]{3,}-[a-z0-9-]+$ ]]; then
            echo -e "${RED}❌ ERROR: Branch naming convention violated.${NC}" >&2
            echo -e "   Branch: $branch_name" >&2
            echo -e "   Feature branches MUST be named like: feature/001-feature-name or feature/1234-feature-name${NC}" >&2
            return 1
        fi
    fi
    return 0
}

# Log messages with colors
log_info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}
