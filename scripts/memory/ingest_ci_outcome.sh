#!/bin/bash
# Ingest a CI outcome artifact into local memory.
#
# Usage: ingest_ci_outcome.sh [path-to-artifact.json]
#        make mem-ingest ARTIFACT=temp/ci-outcome.json
#
# The GitHub Actions runner has no ~/.engram and cannot reach the daemon, which
# binds to 127.0.0.1 and speaks MCP over stdio only. CI therefore emits the
# outcome as a JSON artifact and it is folded into memory here, on a machine
# that actually has the store.

set -uo pipefail

MEM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$MEM_DIR/engram_client.sh"
# shellcheck source=/dev/null
source "$MEM_DIR/session_state.sh"

ARTIFACT="${1:-temp/ci-outcome.json}"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

if [ ! -f "$ARTIFACT" ]; then
    echo -e "${YELLOW}No CI outcome artifact at '$ARTIFACT'.${NC}"
    echo -e "Download it from the workflow run, then:"
    echo -e "  ${YELLOW}make mem-ingest ARTIFACT=<path>${NC}"
    exit 0
fi

mem_requires || exit 1
mem_ensure_daemon || exit 1

slug="$(jq -r '.slug // empty'   "$ARTIFACT")"
status="$(jq -r '.status // "unknown"' "$ARTIFACT")"
branch="$(jq -r '.branch // "unknown"' "$ARTIFACT")"
commit="$(jq -r '.commit // "unknown"' "$ARTIFACT")"
detail="$(jq -r '.detail // "No detail recorded."' "$ARTIFACT")"
run_url="$(jq -r '.run_url // "unknown"' "$ARTIFACT")"

if [ -z "$slug" ]; then
    echo -e "${RED}Artifact has no slug; nothing to attach the outcome to.${NC}" >&2
    exit 1
fi

session_id="$(mem_session_ensure "$slug")" || exit 1

mem_write "$session_id" "learning" "CI outcome for $slug: $status" \
"**What** CI quality gate for $slug finished: $status
**Why** A decision is only worth remembering together with what happened after it shipped.
**Where** $branch at $commit — $run_url
**Learned** $detail" \
    "spec/$slug/outcome" "project" \
    && echo -e "${GREEN}✅ CI outcome for '$slug' ingested into memory.${NC}" \
    || { echo -e "${RED}❌ Could not write the outcome.${NC}" >&2; exit 1; }
