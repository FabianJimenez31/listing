#!/bin/bash
# Git pre-commit hook to enforce quality gates locally before committing.

set -e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd "$PROJECT_DIR"

# Shared helpers. Both are optional so the hook still works in a partial install.
if [ -f ".claude/hooks/emergency_state.sh" ]; then
    # shellcheck source=/dev/null
    source ".claude/hooks/emergency_state.sh"
fi
if [ -f ".specify/scripts/bash/common.sh" ]; then
    # shellcheck source=/dev/null
    source ".specify/scripts/bash/common.sh"
fi

EMERGENCY=0
if command -v harness_emergency_active >/dev/null 2>&1 && harness_emergency_active; then
    EMERGENCY=1
fi

echo -e "${YELLOW}🔍 Running pre-commit Quality Gate Checks...${NC}"
if [ "$EMERGENCY" -eq 1 ]; then
    harness_emergency_notice "workflow gates (branch, naming, Spec-Kit, layout)"
fi
ERRORS=0

# On pull requests, actions/checkout leaves a detached HEAD, so the branch name
# reads back as the literal string "HEAD" and every branch rule fails or, worse,
# passes vacuously. GitHub exposes the real source branch in GITHUB_HEAD_REF.
resolve_branch_name() {
    local name="$1"
    if [ "$name" = "HEAD" ]; then
        if [ -n "${GITHUB_HEAD_REF:-}" ]; then
            printf '%s\n' "$GITHUB_HEAD_REF"
            return 0
        fi
        if [ -n "${GITHUB_REF_NAME:-}" ]; then
            printf '%s\n' "$GITHUB_REF_NAME"
            return 0
        fi
    fi
    printf '%s\n' "$name"
}

# 1. Block direct commit to protected branches
current_branch="$(resolve_branch_name "$(git rev-parse --abbrev-ref HEAD)")"
if [ "$EMERGENCY" -eq 0 ]; then
    case "$current_branch" in
        main|master|prod|staging|develop)
            echo -e "${RED}   ❌ Direct commits to '$current_branch' are forbidden. Please use feature or fix branches!${NC}"
            ERRORS=$((ERRORS + 1))
            ;;
    esac
fi

# 2. Validate branch naming convention
if [ "$EMERGENCY" -eq 0 ]; then
    if [[ ! "$current_branch" =~ ^(feature|fix|hotfix|chore|claude|codex|kiro|test)/[a-z0-9._/-]+$ ]] \
       && [[ ! "$current_branch" =~ ^(main|master|prod|staging|develop)$ ]]; then
        echo -e "${RED}   ❌ Branch name '$current_branch' does not match naming convention (feature|fix|hotfix|chore|claude|codex|kiro|test)/<slug>${NC}"
        ERRORS=$((ERRORS + 1))
    fi

    # Feature branches carry the stricter slug rule shared with CI. Delegating to
    # check_feature_branch keeps this hook and .specify/scripts/bash/check-prerequisites.sh
    # (run by spec-compliance.yml) from disagreeing about what a valid slug is.
    if command -v check_feature_branch >/dev/null 2>&1; then
        if ! check_feature_branch "$current_branch" "true"; then
            ERRORS=$((ERRORS + 1))
        fi
    fi
fi

# 3. Spec-kit Gate: Feature branch must contain specification artifacts
if [ "$EMERGENCY" -eq 0 ] && [[ "$current_branch" =~ ^feature/(.+)$ ]]; then
    if command -v spec_kit_effective_branch_name >/dev/null 2>&1; then
        feature_slug="$(spec_kit_effective_branch_name "$current_branch")"
    else
        feature_slug="${BASH_REMATCH[1]}"
    fi
    spec_dir="specs/$feature_slug"
    missing=()
    for artifact in spec.md plan.md tasks.md; do
        if [ ! -f "$spec_dir/$artifact" ]; then
            missing+=("$spec_dir/$artifact")
        else
            size=$(wc -c < "$spec_dir/$artifact" 2>/dev/null || echo 0)
            if [ "$size" -lt 50 ]; then
                missing+=("$spec_dir/$artifact (empty or unedited)")
            fi
        fi
    done
    if [ ${#missing[@]} -gt 0 ]; then
        echo -e "${RED}   ❌ Spec-Kit Gate Violation: Missing or unedited feature artifacts for branch '$current_branch':${NC}"
        printf '      - %s\n' "${missing[@]}"
        echo -e "${YELLOW}   💡 Run 'make spec-new' or 'bash .specify/scripts/bash/create-new-feature.sh' to initialize."
        ERRORS=$((ERRORS + 1))
    fi
fi

# 4. Prevent temporary scripts in root directory
temp_in_root=$(git diff --cached --name-only --diff-filter=ACM | \
    grep -E '^[^/]+\.(py|sh)$' | \
    grep -vE '^(setup\.py|Makefile|requirements.*\.txt|install\.sh|sonar_local\.sh)$' || true)
if [ -n "$temp_in_root" ] && [ "$EMERGENCY" -eq 0 ]; then
    echo -e "${RED}   ❌ Temporary files detected in repository root:${NC}"
    echo "$temp_in_root" | sed 's/^/      /'
    echo -e "${YELLOW}   💡 Please organize and move temporary scripts to 'temp/' subdirectories.${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 5. Scan for hardcoded credentials / secrets
#    Safety gate: enforced even under an emergency bypass. An incident is never
#    a reason to commit a credential.
secrets=$(git diff --cached --diff-filter=ACM -G 'password|secret|api_key|token' --unified=0 2>/dev/null | \
    grep -E '^\+.*(password|secret|api_key|token)\s*=\s*["'\''][A-Za-z0-9/+_=-]{16,}["'\'']' || true)
if [ -n "$secrets" ]; then
    echo -e "${RED}   ❌ Warning: Potential hardcoded secret or API token detected in Git diff.${NC}"
    echo -e "${RED}      Please use environment variables instead of hardcoding sensitive data.${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 6. Validate Project Structure & Anti-Patterns
if [ "$EMERGENCY" -eq 0 ] && [ -f "scripts/validation/validate_structure.py" ]; then
    if command -v python3 >/dev/null 2>&1; then
        echo -e "${YELLOW}   Running automated architecture validation...${NC}"
        if ! python3 scripts/validation/validate_structure.py; then
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo -e "${YELLOW}   ⚠️  python3 not found; skipping architecture validation.${NC}"
    fi
fi

if [ "$ERRORS" -gt 0 ]; then
    echo -e "${RED}❌ pre-commit Quality Gate FAILED ($ERRORS errors detected)${NC}"
    exit 1
fi

echo -e "${GREEN}✅ pre-commit Quality Gate PASSED${NC}"
exit 0
