#!/bin/bash
# Compose and persist one memory class for the current task.
#
# Usage:
#   capture_stage.sh session-open
#   capture_stage.sh session-close  "<summary>"
#   capture_stage.sh semantic
#   capture_stage.sh procedural
#   capture_stage.sh decision
#   capture_stage.sh outcome  <passed|failed|unknown> [log-file]
#   capture_stage.sh preferences "<constraint text>"
#
# Every class is a by-product of a stage the framework already runs. Nothing
# here asks the developer for new work; it persists what would otherwise
# evaporate when the session ends.

set -uo pipefail

MEM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$MEM_DIR/engram_client.sh"
# shellcheck source=/dev/null
source "$MEM_DIR/session_state.sh"
# shellcheck source=/dev/null
source "$MEM_DIR/task_context.sh"

ACTION="${1:-}"
[ -n "$ACTION" ] || { echo "usage: capture_stage.sh <class> [args]" >&2; exit 1; }

mem_requires || exit 1
mem_ensure_daemon || exit 1

ROOT="$(mem_repo_root)"
SLUG="$(mem_task_slug)"
SPEC_DIR="$ROOT/specs/$SLUG"

# Extract a markdown section body, stopping at the next heading of any level.
section_of() {
    local file="$1" heading="$2"
    [ -f "$file" ] || return 0
    awk -v h="$heading" '
        $0 ~ "^#+ *" h { grab = 1; next }
        grab && /^#+ / { exit }
        grab { print }
    ' "$file" | sed '/^[[:space:]]*$/d' | head -n 25
}

changed_files() {
    git -C "$ROOT" diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null | head -n 20
}

write_class() {
    local class="$1" title="$2" content="$3"
    local session_id
    session_id="$(mem_session_ensure "$SLUG")" || {
        echo "   Could not open an Engram session." >&2; return 1; }
    mem_write "$session_id" "$(mem_class_type "$class")" "$title" "$content" \
              "$(mem_class_topic_key "$class")" "$(mem_class_scope "$class")"
}

case "$ACTION" in
    session-open)
        session_id="$(mem_session_ensure "$SLUG")" || exit 1
        echo "$session_id"
        ;;

    session-close)
        mem_session_end_current "${2:-Session closed by the harness.}"
        ;;

    semantic)
        [ -f "$SPEC_DIR/plan.md" ] || { echo "   No plan.md for $SLUG; skipping semantic." >&2; exit 0; }
        write_class semantic "Architecture of $SLUG" "$(cat <<CONTENT
**What** $(section_of "$SPEC_DIR/plan.md" "Summary")
**Why** $(section_of "$SPEC_DIR/spec.md" "Context")
**Where** specs/$SLUG/plan.md
**Learned** $(section_of "$SPEC_DIR/plan.md" "Technical Context")
CONTENT
)"
        ;;

    procedural)
        [ -f "$SPEC_DIR/tasks.md" ] || { echo "   No tasks.md for $SLUG; skipping procedural." >&2; exit 0; }
        write_class procedural "Procedure for $SLUG" "$(cat <<CONTENT
**What** Implementation procedure recorded for $SLUG.
**Why** Repeating this task, or auditing how it was carried out, should not require re-deriving the order of work.
**Where** specs/$SLUG/tasks.md
**Learned** $(grep -E '^\s*- \[' "$SPEC_DIR/tasks.md" | head -n 25)
CONTENT
)"
        ;;

    decision)
        subject="$(git -C "$ROOT" log -1 --pretty=%s 2>/dev/null)"
        [ -n "$subject" ] || exit 0
        write_class decision "$subject" "$(cat <<CONTENT
**What** $(git -C "$ROOT" log -1 --pretty=%B 2>/dev/null | head -n 20)
**Why** $(section_of "$SPEC_DIR/plan.md" "Summary")
**Where** $(changed_files)
**Learned** commit $(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null) on $(mem_task_branch)
CONTENT
)"
        ;;

    outcome)
        status="${2:-unknown}"
        log_file="${3:-}"
        detail=""
        [ -n "$log_file" ] && [ -f "$log_file" ] && detail="$(tail -n 20 "$log_file")"
        write_class outcome "Outcome of $SLUG: $status" "$(cat <<CONTENT
**What** Test suite result for $SLUG: $status
**Why** Linking a decision to what happened afterwards is what turns a record of choices into a record of consequences.
**Where** $(mem_task_branch) at $(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null)
**Learned** ${detail:-No further detail captured.}
CONTENT
)"
        ;;

    preferences)
        constraint="${2:-}"
        [ -n "$constraint" ] || { echo "usage: capture_stage.sh preferences \"<text>\"" >&2; exit 1; }
        write_class preferences "User working constraints" "$(cat <<CONTENT
**What** $constraint
**Why** Constraints the user stated explicitly should survive the session that produced them.
**Where** $(mem_project)
**Learned** Recorded from $(mem_task_branch).
CONTENT
)"
        ;;

    *)
        echo "unknown class: $ACTION" >&2
        exit 1
        ;;
esac
