#!/usr/bin/env bash
# Helper script to initialize tasks.md if it is missing from feature specs

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
    TASKS_FILE="$SPECS_DIR/tasks.md"
    
    mkdir -p "$SPECS_DIR"
    
    if [ -f "$TASKS_FILE" ]; then
        log_info "tasks.md already exists at specs/$SLUG/tasks.md"
    else
        TEMPLATES_DIR="$REPO_ROOT/.specify/templates"
        if [ -f "$TEMPLATES_DIR/tasks-template.md" ]; then
            sed -e "s/\[FEATURE NAME\]/$SLUG/g" \
                -e "s/\[###-feature-name\]/$SLUG/g" \
                "$TEMPLATES_DIR/tasks-template.md" > "$TASKS_FILE"
            log_success "Successfully created specs/$SLUG/tasks.md"
        else
            log_error "tasks-template.md not found"
            exit 1
        fi
    fi
else
    log_error "Not on a feature branch. Current branch: $CURRENT_BRANCH"
    exit 1
fi
exit 0
