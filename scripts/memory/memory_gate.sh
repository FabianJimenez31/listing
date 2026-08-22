#!/bin/bash
# Memory quota gate.
#
# Usage: memory_gate.sh [commit|push|merge]
#
# Mirrors the Spec-Kit Gate in .claude/hooks/pre-commit.sh: it collects what is
# missing, prints it in the same shape, and blocks. Memory that is mandatory in
# documentation but not enforced by a gate is documentation, not a guarantee.

set -uo pipefail

MEM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$MEM_DIR/engram_client.sh"
# shellcheck source=/dev/null
source "$MEM_DIR/session_state.sh"
# shellcheck source=/dev/null
source "$MEM_DIR/task_context.sh"

ROOT="$(mem_repo_root)"
if [ -f "$ROOT/.claude/hooks/emergency_state.sh" ]; then
    # shellcheck source=/dev/null
    source "$ROOT/.claude/hooks/emergency_state.sh"
fi

STAGE="${1:-push}"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

# Classes that must already exist by the end of each stage. Cumulative.
classes_for_stage() {
    case "$1" in
        commit) echo "contextual episodic semantic procedural decision preferences" ;;
        push)   echo "contextual episodic semantic procedural decision preferences outcome" ;;
        merge)  echo "$MEM_CLASS_ALL" ;;
        *)      echo "$MEM_CLASS_ALL" ;;
    esac
}

KIND="$(mem_task_kind)"
SLUG="$(mem_task_slug)"

if [ "$KIND" = "other" ]; then
    echo -e "${YELLOW}   Memory gate: branch '$(mem_task_branch)' carries no task quota; session only.${NC}"
    exit 0
fi

# Emergency bypass. Skipping the gate is recorded, so an incident never becomes
# a silent hole in the project's memory.
if command -v harness_emergency_active >/dev/null 2>&1 && harness_emergency_active; then
    harness_emergency_notice "memory gate ($STAGE)"
    if mem_requires 2>/dev/null && mem_health; then
        session_id="$(mem_session_ensure "$SLUG" 2>/dev/null)" || session_id=""
        if [ -n "$session_id" ]; then
            mem_write "$session_id" "bugfix" "Memory gate bypassed on $SLUG" \
"**What** The $STAGE memory gate was skipped under an emergency bypass.
**Why** $(harness_emergency_reason)
**Where** $(mem_task_branch)
**Learned** Memory for this task is incomplete by design; reconstruct it during the post-mortem." \
                "spec/$SLUG/bypass" "project" || true
        fi
    fi
    exit 0
fi

mem_requires || {
    echo -e "${RED}   Memory gate cannot run: curl and jq are required.${NC}" >&2; exit 1; }
mem_ensure_daemon || {
    echo -e "${RED}❌ Memory gate FAILED: Engram is unavailable.${NC}" >&2
    echo -e "${YELLOW}   Declare an emergency with 'make hotfix' if this is blocking an incident.${NC}" >&2
    exit 1; }

REQUIRED="$(mem_task_required_classes)"
STAGE_CLASSES="$(classes_for_stage "$STAGE")"

echo -e "${YELLOW}🧠 Memory gate (${STAGE}) for ${KIND} branch '${SLUG}'...${NC}"

MISSING=""
for class in $REQUIRED; do
    case " $STAGE_CLASSES " in *" $class "*) ;; *) continue ;; esac

    ok=1
    case "$class" in
        contextual)
            [ -n "$(mem_session_stored_id)" ] || ok=0
            ;;
        episodic)
            # Derived from the session timeline: satisfied once anything was written.
            [ "$(mem_count_observations)" -gt 0 ] 2>/dev/null || ok=0
            ;;
        *)
            mem_has_topic "$(mem_class_topic_key "$class")" "$(mem_class_scope "$class")" || ok=0
            ;;
    esac

    [ "$ok" -eq 1 ] || MISSING="$MISSING $class"
done

if [ -n "$MISSING" ]; then
    echo -e "${RED}   ❌ Memory Gate Violation: missing memory for '${SLUG}' at stage '${STAGE}':${NC}"
    for class in $MISSING; do
        printf '      - %s\n' "$(mem_class_label "$class")"
    done
    echo -e "${YELLOW}   💡 Generate it with 'make mem-capture', or inspect with 'make mem-context'.${NC}"
    echo -e "${YELLOW}      Quota for ${KIND} branches: ${REQUIRED}${NC}"
    exit 1
fi

echo -e "${GREEN}   ✅ Memory gate PASSED (${REQUIRED// /, })${NC}"
exit 0
