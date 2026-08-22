#!/bin/bash
# SessionStart agent hook.
#
# Opens the Engram session for the current task and prints the project's stored
# context so the agent begins with what the project already knows instead of
# rediscovering it. Output on stdout is added to the agent's context.

ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
cd "$ROOT" 2>/dev/null || exit 0

[ -x "scripts/memory/capture_stage.sh" ] || exit 0

bash scripts/memory/capture_stage.sh session-open >/dev/null 2>&1 || exit 0

# shellcheck source=/dev/null
source "scripts/memory/engram_client.sh" 2>/dev/null || exit 0
mem_health || exit 0

CONTEXT="$(mem_context 2>/dev/null)"
[ -n "$CONTEXT" ] || exit 0

echo "## Project memory (Engram)"
echo ""
printf '%s\n' "$CONTEXT" | jq -r '
    if type == "object" then (.context // .content // (.|tostring))
    else (.|tostring) end' 2>/dev/null | head -n 120
exit 0
