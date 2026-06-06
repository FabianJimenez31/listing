#!/usr/bin/env bash
# Interactive CLI tool to create feature branches and populate spec templates

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REPO_ROOT=$(get_repo_root)

echo -e "${BLUE}=== IA-Framework: New Feature Initializer ===${NC}"
echo ""

# 1. Ask for feature name
read -rp "Enter feature slug (e.g. 001-user-login): " SLUG
if [ -z "$SLUG" ]; then
    log_error "Slug cannot be empty."
    exit 1
fi

# Normalize slug
SLUG=$(echo "$SLUG" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-//]//g')

# Ensure prefix is at least 3 digits
if [[ ! "$SLUG" =~ ^[0-9]{3,}- ]]; then
    log_warning "We recommend starting feature slugs with a 3-digit sequential number (e.g. 001-$SLUG)"
    read -rp "Do you want to prepend a sequential prefix? (e.g. 001) [y/N]: " PREPEND
    if [[ "$PREPEND" =~ ^[Yy] ]]; then
        read -rp "Enter prefix number: " PREFIX_NUM
        SLUG="${PREFIX_NUM}-${SLUG}"
    fi
fi

BRANCH_NAME="feature/$SLUG"
SPECS_DIR="$REPO_ROOT/specs/$SLUG"

log_info "Creating feature directory: specs/$SLUG"
mkdir -p "$SPECS_DIR"

# Dates
CURRENT_DATE=$(date +"%Y-%m-%d")

# Check if templates exist and copy them
TEMPLATES_DIR="$REPO_ROOT/.specify/templates"

if [ -f "$TEMPLATES_DIR/spec-template.md" ]; then
    sed -e "s/\[FEATURE NAME\]/$SLUG/g" \
        -e "s/\[DATE\]/$CURRENT_DATE/g" \
        -e "s/\[###-feature-name\]/$SLUG/g" \
        "$TEMPLATES_DIR/spec-template.md" > "$SPECS_DIR/spec.md"
    log_success "Created specs/$SLUG/spec.md"
else
    log_warning "spec-template.md not found, skipped spec.md creation"
fi

if [ -f "$TEMPLATES_DIR/plan-template.md" ]; then
    sed -e "s/\[FEATURE NAME\]/$SLUG/g" \
        -e "s/\[DATE\]/$CURRENT_DATE/g" \
        -e "s/\[###-feature-name\]/$SLUG/g" \
        "$TEMPLATES_DIR/plan-template.md" > "$SPECS_DIR/plan.md"
    log_success "Created specs/$SLUG/plan.md"
else
    log_warning "plan-template.md not found, skipped plan.md creation"
fi

if [ -f "$TEMPLATES_DIR/tasks-template.md" ]; then
    sed -e "s/\[FEATURE NAME\]/$SLUG/g" \
        -e "s/\[###-feature-name\]/$SLUG/g" \
        "$TEMPLATES_DIR/tasks-template.md" > "$SPECS_DIR/tasks.md"
    log_success "Created specs/$SLUG/tasks.md"
else
    log_warning "tasks-template.md not found, skipped tasks.md creation"
fi

# Create Git Branch if in Git repo
if has_git; then
    # Check if branch already exists
    if git -C "$REPO_ROOT" rev-parse --verify "$BRANCH_NAME" >/dev/null 2>&1; then
        log_warning "Git branch '$BRANCH_NAME' already exists. Switching to it."
        git -C "$REPO_ROOT" checkout "$BRANCH_NAME"
    else
        log_info "Creating and checking out Git branch '$BRANCH_NAME'"
        git -C "$REPO_ROOT" checkout -b "$BRANCH_NAME"
    fi
else
    log_warning "Not in a Git repository. Skipped Git branch creation."
fi

log_success "Feature '$SLUG' successfully initialized! 🚀"
log_info "Next Steps:"
log_info "  1. Fill in specifications in: specs/$SLUG/spec.md"
log_info "  2. Outline your technical design in: specs/$SLUG/plan.md"
log_info "  3. Start coding! The pre-commit hook will protect your quality."
exit 0
