#!/bin/bash
# PreToolUse hook for AI assistants to prevent code bloating.
# Rules: ≤800 lines OK, 801-1000 warn, >1000 block.
# Supports a customizable allowlist for legacy files.

json_input=$(cat)
file_path=$(echo "$json_input" | jq -r '.tool_input.file_path // empty')
[ -z "$file_path" ] && exit 0

# Custom allowlist: Add any legacy files that are exempt from the line-limit check.
case "$file_path" in
    */legacy_file_to_ignore.py) exit 0 ;;
    # Add your project-specific legacy file exemptions here:
    # */some_bloated_legacy_file.js) exit 0 ;;
esac

if [ -f "$file_path" ]; then
    line_count=$(wc -l < "$file_path")
else
    content=$(echo "$json_input" | jq -r '.tool_input.content // empty')
    [ -z "$content" ] && exit 0
    line_count=$(echo "$content" | wc -l)
fi

if [ "$line_count" -gt 1000 ]; then
    echo "❌ BLOCK: '$file_path' has $line_count lines (limit is 1000 lines)."
    echo "   Please divide the functionality into smaller, highly cohesive modules."
    echo "   Exemptions can be added to the allowlist in '.claude/hooks/check-file-size.sh' for legacy files only."
    exit 2
fi

if [ "$line_count" -gt 800 ]; then
    echo "⚠️  WARNING: '$file_path' has $line_count lines (>800). Consider refactoring and dividing it soon."
fi

exit 0
