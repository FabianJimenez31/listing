#!/bin/bash
# Shared emergency-bypass state for the IA-Framework harness.
#
# The bypass must survive across processes: a hotfix is declared by one script
# and honoured later by the git hooks, which run in their own shells. An
# exported environment variable cannot do that, so the state lives in a file.
#
# The bypass is considered ACTIVE when either:
#   - HARNESS_EMERGENCY=1 is present in the current environment, or
#   - the state file exists and has not expired.
#
# Scope of the bypass (deliberately narrow):
#   BYPASSED  - workflow gates: protected-branch block, branch naming, Spec-Kit
#   ENFORCED  - safety gates: hardcoded secrets, file size limits
# An emergency is a reason to skip process, never a reason to leak a credential.

HARNESS_EMERGENCY_TTL="${HARNESS_EMERGENCY_TTL:-7200}"

harness_emergency_state_file() {
    local root
    root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
    printf '%s\n' "$root/temp/.harness_emergency"
}

# Returns 0 when the bypass is active, 1 otherwise.
harness_emergency_active() {
    if [ "${HARNESS_EMERGENCY:-0}" = "1" ]; then
        return 0
    fi

    local state_file expires_at now
    state_file="$(harness_emergency_state_file)"
    [ -f "$state_file" ] || return 1

    expires_at="$(head -n 1 "$state_file" 2>/dev/null | tr -dc '0-9')"
    [ -n "$expires_at" ] || return 1

    now="$(date +%s)"
    if [ "$now" -ge "$expires_at" ]; then
        rm -f "$state_file"
        return 1
    fi
    return 0
}

# Human-readable description of why the bypass is active.
harness_emergency_reason() {
    if [ "${HARNESS_EMERGENCY:-0}" = "1" ]; then
        printf 'HARNESS_EMERGENCY=1 set in the environment\n'
        return 0
    fi
    local state_file expires_at now
    state_file="$(harness_emergency_state_file)"
    expires_at="$(head -n 1 "$state_file" 2>/dev/null | tr -dc '0-9')"
    now="$(date +%s)"
    if [ -n "$expires_at" ]; then
        printf 'declared hotfix, %d minute(s) remaining\n' "$(( (expires_at - now) / 60 ))"
    fi
}

# Declare an emergency. Optional argument overrides the TTL in seconds.
harness_emergency_declare() {
    local ttl="${1:-$HARNESS_EMERGENCY_TTL}"
    local state_file
    state_file="$(harness_emergency_state_file)"
    mkdir -p "$(dirname "$state_file")"
    printf '%s\n' "$(( $(date +%s) + ttl ))" > "$state_file"
    printf 'declared for %d minute(s)\n' "$(( ttl / 60 ))"
}

harness_emergency_clear() {
    rm -f "$(harness_emergency_state_file)"
}

# Print the standard banner when a gate is skipped. Callers pass the gate name.
harness_emergency_notice() {
    local gate="$1"
    echo "⚠️  EMERGENCY BYPASS ACTIVE — skipping: ${gate}"
    echo "   Reason: $(harness_emergency_reason)"
    echo "   Safety gates (secrets, file size) remain enforced."
    echo "   Clear with: make emergency-clear"
}
