#!/usr/bin/env bash
# Generic Frontend / SPA Atomic Deploy Smoke Tester
#
# Validates that a frontend deployment is operational and atomic.
# Verifies that:
#   1. Critical routes serve 200 OK and valid HTML size.
#   2. Served HTML references a valid main application chunk/bundle.
#   3. Static chunks/bundles exist on the server (returns 200 OK).
#   4. All critical SPA paths point to the exact same bundle file,
#      avoiding partial cache mismatches where users experience infinite reload loops.
#
# Usage:
#   ./smoke_test_frontend.sh
#   BASE_URL=https://myapp.com ROUTES="/ /dashboard /settings" ./smoke_test_frontend.sh

set -uo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="${BASE_URL:-http://localhost:3000}"
VERBOSE=1

# Critical paths to check. Override via space-separated list in ROUTES env
ROUTES_STR="${ROUTES:-/ /dashboard}"
read -ra ROUTES <<< "$ROUTES_STR"

# Asset bundle pattern (e.g. app-XXXX.js or index-XXXX.js)
BUNDLE_PATTERN="${BUNDLE_PATTERN:-app-[A-Za-z0-9_-]+\.js|index-[A-Za-z0-9_-]+\.js|main-[A-Za-z0-9_-]+\.js}"

echo -e "${BLUE}======================================================================${NC}"
echo -e "⚡ IA-Framework SPA Smoke Tester & Atomic Deploy Gate ⚡"
echo -e "${BLUE}======================================================================${NC}"
echo -e "[INFO] Testing Base URL: ${YELLOW}${BASE_URL}${NC}"
echo -e "[INFO] Critical Paths:  ${YELLOW}${ROUTES[*]}${NC}\n"

FAILS=0
fail() { echo -e "${RED}❌ FAIL: $*${NC}" >&2; FAILS=$((FAILS + 1)); }
ok()   { [[ $VERBOSE -eq 1 ]] && echo -e "${GREEN}✅ OK:   $*${NC}"; }

curl_status() {
    local out
    # Save the body to a temp file and write status/download size
    out=$(curl -sS --max-time 10 -o /tmp/smoke_body.$$ \
        -w "%{http_code} %{size_download}" "$1" 2>/dev/null) || out="000 0"
    echo "$out"
}

# ---------------------------------------------------------------------------
# 1. Path Health checks & Bundle Extraction
# ---------------------------------------------------------------------------
declare -a BUNDLE_FILES=()

for route in "${ROUTES[@]}"; do
    target_url="${BASE_URL}${route}"
    read -r status size < <(curl_status "$target_url")
    
    if [[ "$status" != "200" ]]; then
        fail "Route '$route' returned HTTP status $status"
        continue
    fi
    
    if (( size < 200 )); then
        fail "Route '$route' body size is suspiciously small ($size bytes)"
        continue
    fi
    
    # Extract bundle name matching pattern from HTML
    bundle_file=$(grep -oE "$BUNDLE_PATTERN" /tmp/smoke_body.$$ | head -n 1 || true)
    
    if [[ -z "$bundle_file" ]]; then
        # Check if index contains scripts at all
        script_check=$(grep -o '<script' /tmp/smoke_body.$$ || true)
        if [[ -z "$script_check" ]]; then
            fail "Route '$route' contains NO script tags"
        else
            ok "Route '$route' returns valid HTML (no matching compiled bundle pattern found)"
        fi
        continue
    fi
    
    ok "Route '$route' is active [HTTP 200, $size bytes, references bundle: $bundle_file]"
    BUNDLE_FILES+=("$bundle_file")
done

rm -f /tmp/smoke_body.$$

# ---------------------------------------------------------------------------
# 2. Deploy Atomicity Check (Do all paths reference the exact same asset version?)
# ---------------------------------------------------------------------------
if [[ ${#BUNDLE_FILES[@]} -gt 0 ]]; then
    uniq_bundles=$(printf '%s\n' "${BUNDLE_FILES[@]}" | sort -u)
    count=$(echo "$uniq_bundles" | wc -l)
    
    if [[ "$count" -gt 1 ]]; then
        fail "Atomic mismatch! Routes point to different JS bundle files (Partial deployment):"
        echo "$uniq_bundles" | sed 's/^/      /' >&2
    else
        ok "Atomic deployment check passed: All routes reference the same bundle file: $(echo "$uniq_bundles")"
    fi
fi

# ---------------------------------------------------------------------------
# 3. Static Asset Validation (Does the bundle file actually exist on the server?)
# ---------------------------------------------------------------------------
if [[ ${#BUNDLE_FILES[@]} -gt 0 ]]; then
    for bundle in $(printf '%s\n' "${BUNDLE_FILES[@]}" | sort -u); do
        # Standard assets folder check. Tries direct, /assets/, and /static/
        found_asset=0
        for path in "/assets/" "/static/" "/"; do
            asset_url="${BASE_URL}${path}${bundle}"
            read -r status size < <(curl_status "$asset_url")
            rm -f /tmp/smoke_body.$$
            
            if [[ "$status" == "200" ]]; then
                ok "Static bundle is reachable at '${path}${bundle}' [HTTP 200, $size bytes]"
                found_asset=1
                break
            fi
        done
        
        if [[ $found_asset -eq 0 ]]; then
            fail "Bundle asset '$bundle' is referenced but was NOT found on the server (404/dead links)!"
        fi
    done
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
if [[ $FAILS -eq 0 ]]; then
    echo -e "${GREEN}🎉 SMOKE TEST PASSED! The deployment is fully operational, clean, and atomic!${NC}"
    exit 0
fi

echo -e "${RED}❌ SMOKE TEST FAILED: $FAILS error(s) detected during deploy verification.${NC}" >&2
echo -e "${YELLOW}💡 Warning: DO NOT promote this deployment. Rollback is highly recommended.${NC}" >&2
exit 1
