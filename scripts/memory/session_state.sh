#!/bin/bash
# Engram session identity for the current working tree.
#
# A session groups every observation produced while working on one task. The id
# has to outlive the process that created it, because the hooks that write
# memory run as separate short-lived shells, so it is persisted to disk.

# shellcheck source=/dev/null
[ -n "${ENGRAM_BASE_URL:-}" ] || source "$(dirname "${BASH_SOURCE[0]}")/engram_client.sh"

mem_session_file() {
    printf '%s\n' "$(mem_repo_root)/temp/.engram_session"
}

mem_new_session_id() {
    if command -v uuidgen >/dev/null 2>&1; then
        uuidgen | tr '[:upper:]' '[:lower:]'
    else
        printf 'sess-%s-%s-%s\n' "$(date +%Y%m%d%H%M%S)" "$$" "${RANDOM}"
    fi
}

# Stored as "<session_id> <slug>" so a new task starts a new session even when
# the previous one was never closed.
mem_session_stored_id()   { awk 'NR==1{print $1}' "$(mem_session_file)" 2>/dev/null; }
mem_session_stored_slug() { awk 'NR==1{print $2}' "$(mem_session_file)" 2>/dev/null; }

# Open a session for the given slug, reusing the stored one when it matches.
# Prints the session id.
mem_session_ensure() {
    local slug="${1:-none}"
    local stored_id stored_slug session_file
    session_file="$(mem_session_file)"
    stored_id="$(mem_session_stored_id)"
    stored_slug="$(mem_session_stored_slug)"

    if [ -n "$stored_id" ] && [ "$stored_slug" = "$slug" ]; then
        printf '%s\n' "$stored_id"
        return 0
    fi

    local new_id
    new_id="$(mem_new_session_id)"
    if ! mem_session_open "$new_id" "$(mem_repo_root)"; then
        return 1
    fi
    mkdir -p "$(dirname "$session_file")"
    printf '%s %s\n' "$new_id" "$slug" > "$session_file"
    printf '%s\n' "$new_id"
}

mem_session_end_current() {
    local summary="$1"
    local stored_id
    stored_id="$(mem_session_stored_id)"
    [ -n "$stored_id" ] || return 0
    mem_session_close "$stored_id" "$summary"
    rm -f "$(mem_session_file)"
}
