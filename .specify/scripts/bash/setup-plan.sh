#!/usr/bin/env bash
# Helper script to initialize plan.md if it is missing from feature specs

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REPO_ROOT=$(get_repo_root)

if ! has_git; then
    log_error "Not inside a Git repository."
    exit 1
fi

CURRENT_BRANCH=$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)

if [[ "$CURRENT_BRANCH" =~ ^feature/(.+)$ ]]; then
    SLUG="${BASH_REMATCH[1]}"
    SPECS_DIR="$REPO_ROOT/specs/$SLUG"
    PLAN_FILE="$SPECS_DIR/plan.md"
    
    mkdir -p "$SPECS_DIR"
    
    if [ -f "$PLAN_FILE" ]; then
        log_info "plan.md already exists at specs/$SLUG/plan.md"
    else
        TEMPLATES_DIR="$REPO_ROOT/.specify/templates"
        CURRENT_DATE=$(date +"%Y-%m-%d")
        if [ -f "$TEMPLATES_DIR/plan-template.md" ]; then
            sed -e "s/\[FEATURE NAME\]/$SLUG/g" \
                -e "s/\[DATE\]/$CURRENT_DATE/g" \
                -e "s/\[###-feature-name\]/$SLUG/g" \
                "$TEMPLATES_DIR/plan-template.md" > "$PLAN_FILE"
            log_success "Successfully created specs/$SLUG/plan.md"
        else
            log_error "plan-template.md not found"
            exit 1
        fi
    fi
else
    log_error "Not on a feature branch. Current branch: $CURRENT_BRANCH"
    exit 1
fi
exit 0
