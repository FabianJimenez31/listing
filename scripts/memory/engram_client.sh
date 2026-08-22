#!/bin/bash
# Low-level HTTP client for the Engram memory daemon.
#
# The harness writes memory through Engram's local HTTP API rather than through
# MCP. MCP depends on the agent choosing to call mem_save, which cannot be
# guaranteed and does not survive context compaction. The hooks below run as
# ordinary processes and write deterministically.
#
# This file is the only place in the framework that knows the port, the payload
# shapes and the endpoint names. Everything else goes through these functions.

ENGRAM_PORT="${ENGRAM_PORT:-7437}"
ENGRAM_BASE_URL="http://127.0.0.1:${ENGRAM_PORT}"
ENGRAM_START_TIMEOUT="${ENGRAM_START_TIMEOUT:-3}"

MEM_RED='\033[0;31m'
MEM_GREEN='\033[0;32m'
MEM_YELLOW='\033[1;33m'
MEM_NC='\033[0m'

mem_repo_root() {
    git rev-parse --show-toplevel 2>/dev/null || pwd
}

# --- Dependencies ------------------------------------------------------------

mem_requires() {
    local missing=0
    command -v curl >/dev/null 2>&1 || { echo "curl not found" >&2; missing=1; }
    command -v jq   >/dev/null 2>&1 || { echo "jq not found" >&2; missing=1; }
    return $missing
}

mem_binary_present() {
    command -v engram >/dev/null 2>&1
}

# --- Daemon lifecycle --------------------------------------------------------

mem_health() {
    curl -sf --max-time 2 "${ENGRAM_BASE_URL}/health" >/dev/null 2>&1
}

# Start the daemon once and wait up to ENGRAM_START_TIMEOUT seconds for it to
# answer. Returns non-zero when memory is unavailable; callers must treat that
# as a hard failure rather than continuing silently.
mem_ensure_daemon() {
    mem_health && return 0

    if ! mem_binary_present; then
        echo -e "${MEM_RED}   Engram is not installed. Run ./install.sh to set it up.${MEM_NC}" >&2
        return 1
    fi

    ( engram serve >/dev/null 2>&1 & ) >/dev/null 2>&1

    local waited=0
    while [ "$waited" -lt "$ENGRAM_START_TIMEOUT" ]; do
        sleep 1
        waited=$((waited + 1))
        mem_health && return 0
    done

    echo -e "${MEM_RED}   Engram daemon did not answer on ${ENGRAM_BASE_URL} after ${ENGRAM_START_TIMEOUT}s.${MEM_NC}" >&2
    echo -e "${MEM_YELLOW}   Start it manually with: engram serve${MEM_NC}" >&2
    return 1
}

# --- Project resolution ------------------------------------------------------

# Engram resolves the project from cwd with six fallback levels, which lets two
# machines write to different buckets for the same repository. A versioned
# .engram/config.json has the highest precedence in that algorithm, so the
# framework pins the name there and reads the same value here.
mem_project() {
    local root config
    root="$(mem_repo_root)"
    config="$root/.engram/config.json"
    if [ -f "$config" ]; then
        jq -r '.project_name // empty' "$config" 2>/dev/null && return 0
    fi
    basename "$root"
}

# --- Sessions ----------------------------------------------------------------

mem_session_open() {
    local session_id="$1" directory="$2"
    local payload
    payload="$(jq -n \
        --arg id "$session_id" \
        --arg project "$(mem_project)" \
        --arg directory "$directory" \
        '{id:$id, project:$project, directory:$directory}')"
    curl -sf --max-time 5 -X POST "${ENGRAM_BASE_URL}/sessions" \
        -H 'Content-Type: application/json' -d "$payload" >/dev/null
}

mem_session_close() {
    local session_id="$1" summary="$2"
    local payload
    payload="$(jq -n --arg summary "$summary" '{summary:$summary}')"
    curl -sf --max-time 5 -X POST "${ENGRAM_BASE_URL}/sessions/${session_id}/end" \
        -H 'Content-Type: application/json' -d "$payload" >/dev/null
}

# --- Observations ------------------------------------------------------------

# mem_write <session_id> <type> <title> <content> <topic_key> [scope]
# topic_key upserts within project+scope+topic_key, so a stage that advances
# updates its state and bumps revision_count instead of duplicating it.
mem_write() {
    local session_id="$1" type="$2" title="$3" content="$4" topic_key="$5" scope="${6:-project}"
    local payload
    payload="$(jq -n \
        --arg session_id "$session_id" \
        --arg type "$type" \
        --arg title "$title" \
        --arg content "$content" \
        --arg topic_key "$topic_key" \
        --arg scope "$scope" \
        --arg project "$(mem_project)" \
        '{session_id:$session_id, type:$type, title:$title, content:$content,
          topic_key:$topic_key, scope:$scope, project:$project}')"
    curl -sf --max-time 5 -X POST "${ENGRAM_BASE_URL}/observations" \
        -H 'Content-Type: application/json' -d "$payload" >/dev/null
}

# Recent observations for a scope, as raw JSON.
mem_recent() {
    local scope="${1:-project}" limit="${2:-200}"
    curl -sf --max-time 5 \
        "${ENGRAM_BASE_URL}/observations/recent?project=$(mem_project)&scope=${scope}&limit=${limit}" 2>/dev/null
}

# Returns 0 when an observation with the given topic_key exists.
# Matching is done on the topic_key field rather than through FTS, because FTS
# indexes title and content and would report false positives.
mem_has_topic() {
    local topic_key="$1" scope="${2:-project}"
    mem_recent "$scope" \
        | jq -e --arg k "$topic_key" 'any(..|objects|select(.topic_key? == $k); true)' >/dev/null 2>&1
}

mem_count_observations() {
    mem_recent "project" | jq '[..|objects|select(.topic_key? != null)] | length' 2>/dev/null || echo 0
}

mem_context() {
    curl -sf --max-time 5 "${ENGRAM_BASE_URL}/context?project=$(mem_project)&scope=project" 2>/dev/null
}

mem_search() {
    local query="$1" limit="${2:-10}"
    curl -sf --max-time 5 -G "${ENGRAM_BASE_URL}/search" \
        --data-urlencode "q=${query}" \
        --data-urlencode "project=$(mem_project)" \
        --data-urlencode "limit=${limit}" 2>/dev/null
}

mem_doctor() {
    curl -sf --max-time 5 "${ENGRAM_BASE_URL}/doctor?project=$(mem_project)" 2>/dev/null
}
