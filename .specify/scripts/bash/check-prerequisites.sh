#!/usr/bin/env bash
# Consolidated prerequisite checking script for IA-Framework

set -e

# Parse command line arguments
JSON_MODE=false
REQUIRE_TASKS=false

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --require-tasks)
            REQUIRE_TASKS=true
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REPO_ROOT=$(get_repo_root)
HAS_GIT_REPO="false"
CURRENT_BRANCH="main"

if has_git; then
    HAS_GIT_REPO="true"
    CURRENT_BRANCH=$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)
fi

# Skip checks for protected or common branches
if [[ "$CURRENT_BRANCH" =~ ^(main|master|prod|staging|develop)$ ]]; then
    if $JSON_MODE; then
        echo '{"status":"ok","message":"Protected branch, checks skipped"}'
    else
        log_info "On protected branch '$CURRENT_BRANCH'; spec prerequisites skipped."
    fi
    exit 0
fi

# Ensure branch conforms to Git Flow feature convention
if ! check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT_REPO"; then
    exit 1
fi

# If it's a feature branch, validate existence of specs
if [[ "$CURRENT_BRANCH" =~ ^feature/(.+)$ ]]; then
    SLUG="${BASH_REMATCH[1]}"
    SPECS_DIR="$REPO_ROOT/specs/$SLUG"
    
    MISSING_FILES=()
    
    # Files to check
    FILES_TO_CHECK=("spec.md" "plan.md")
    if $REQUIRE_TASKS; then
        FILES_TO_CHECK+=("tasks.md")
    fi
    
    # Verify directory
    if [ ! -d "$SPECS_DIR" ]; then
        if $JSON_MODE; then
            echo "{\"status\":\"error\",\"message\":\"Directory specs/$SLUG not found\"}"
        else
            log_error "Feature directory not found: specs/$SLUG"
            log_warning "💡 Run 'make spec-new' or 'bash .specify/scripts/bash/create-new-feature.sh' to initialize."
        fi
        exit 1
    fi
    
    # Verify each file
    for file in "${FILES_TO_CHECK[@]}"; do
        file_path="$SPECS_DIR/$file"
        if [ ! -f "$file_path" ]; then
            MISSING_FILES+=("$file")
        else
            # Ensure file is not empty or just contains template comments
            size=$(wc -c < "$file_path" 2>/dev/null || echo 0)
            if [ "$size" -lt 50 ]; then
                MISSING_FILES+=("$file (empty or unedited)")
            fi
        fi
    done
    
    if [ ${#MISSING_FILES[@]} -gt 0 ]; then
        if $JSON_MODE; then
            echo "{\"status\":\"error\",\"missing\":$(printf '%s\n' "${MISSING_FILES[@]}" | jq -R . | jq -s .)}"
        else
            log_error "Prerequisite check FAILED for branch '$CURRENT_BRANCH'. Missing or unedited spec documents:"
            for item in "${MISSING_FILES[@]}"; do
                echo -e "   ${RED}✗ specs/$SLUG/$item${NC}"
            fi
            log_warning "💡 Please complete specifications and plans before proceeding."
        fi
        exit 1
    fi
fi

if $JSON_MODE; then
    echo '{"status":"ok","message":"All spec prerequisites satisfied"}'
else
    log_success "All spec prerequisites satisfied for branch '$CURRENT_BRANCH'."
fi
exit 0
