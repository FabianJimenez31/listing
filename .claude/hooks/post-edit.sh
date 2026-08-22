#!/bin/bash
# PostToolUse agent hook.
#
# Captures memory as a by-product of editing the artifacts the framework already
# requires. Closing plan.md records the semantic state; closing tasks.md records
# the procedural one. The agent is not asked to remember anything.
#
# This hook must never fail an edit: memory is captured best-effort here, and
# enforced later by the memory gate at push time.

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CAPTURE="$ROOT/scripts/memory/capture_stage.sh"
[ -x "$CAPTURE" ] || exit 0

json_input="$(cat 2>/dev/null || true)"
[ -n "$json_input" ] || exit 0

command -v jq >/dev/null 2>&1 || exit 0
file_path="$(printf '%s' "$json_input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)"
[ -n "$file_path" ] || exit 0

case "$file_path" in
    */specs/*/plan.md)  bash "$CAPTURE" semantic   >/dev/null 2>&1 || true ;;
    */specs/*/tasks.md) bash "$CAPTURE" procedural >/dev/null 2>&1 || true ;;
esac

exit 0
