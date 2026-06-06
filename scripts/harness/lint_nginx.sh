#!/usr/bin/env bash
# Generic Nginx Config Sanity Check (Harness Lint)
#
# Scans Nginx configurations for critical, known architectural pitfalls
# such as the "localhost connection lottery" which causes intermittent failures.
#
# Rationale: 'localhost' can resolve to both IPv6 (::1) and IPv4 (127.0.0.1).
# If the target upstream server is only listening on IPv4, Nginx might attempt
# connection via IPv6, resulting in intermittent ERR_CONNECTION_CLOSED errors.
# Enforce using explicit '127.0.0.1'.
#
# Usage:
#   ./lint_nginx.sh
#   NGINX_ENABLED=/etc/nginx/sites-enabled ./lint_nginx.sh --verbose

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

NGINX_ENABLED="${NGINX_ENABLED:-/etc/nginx/sites-enabled}"
VERBOSE=0
[[ "${1:-}" == "--verbose" || "${1:-}" == "-v" ]] && VERBOSE=1

echo -e "${BLUE}======================================================================${NC}"
echo -e "⚡ IA-Framework Nginx Configuration Linter ⚡"
echo -e "${BLUE}======================================================================${NC}"

if [[ ! -d "$NGINX_ENABLED" ]]; then
    echo -e "${YELLOW}[WARNING] Nginx directory '$NGINX_ENABLED' does not exist.${NC}"
    echo -e "   Skipping active Nginx validation. Set NGINX_ENABLED to point to a valid folder."
    exit 0
fi

# Locate all enabled site files (following symlinks)
mapfile -t SITES < <(find -L "$NGINX_ENABLED" -maxdepth 1 -type f 2>/dev/null | sort)

if [[ ${#SITES[@]} -eq 0 ]]; then
    echo -e "${YELLOW}[WARNING] No active configuration files found in $NGINX_ENABLED${NC}"
    exit 0
fi

if [[ $VERBOSE -eq 1 ]]; then
    echo -e "${BLUE}[INFO] Scanning ${#SITES[@]} enabled configurations...${NC}"
fi

FAILS=0

# Check 1: proxy_pass referencing http(s)://localhost:PORT
HITS_PROXY=$(grep -nHE '^\s*proxy_pass\s+https?://localhost:[0-9]+' "${SITES[@]}" 2>/dev/null || true)
if [[ -n "$HITS_PROXY" ]]; then
    echo -e "${RED}❌ FAIL [proxy_pass localhost]:${NC} Found localhost upstreams in:"
    echo "$HITS_PROXY" | sed 's/^/  /'
    FAILS=$((FAILS + $(echo "$HITS_PROXY" | wc -l)))
fi

# Check 2: upstream block server referencing localhost:PORT
HITS_UPSTREAM=$(grep -nHE '^\s*server\s+localhost:[0-9]+' "${SITES[@]}" 2>/dev/null || true)
if [[ -n "$HITS_UPSTREAM" ]]; then
    echo -e "${RED}❌ FAIL [upstream server localhost]:${NC} Found localhost server statements in:"
    echo "$HITS_UPSTREAM" | sed 's/^/  /'
    FAILS=$((FAILS + $(echo "$HITS_UPSTREAM" | wc -l)))
fi

echo ""
if [[ $FAILS -eq 0 ]]; then
    echo -e "${GREEN}✅ NGINX LINT PASSED: No hazardous 'localhost' upstream patterns detected.${NC}"
    exit 0
fi

echo -e "${RED}❌ NGINX LINT FAILED: $FAILS occurrence(s) of 'localhost' in proxy_pass or upstream blocks!${NC}" >&2
echo -e "${YELLOW}💡 Recommendation: Replace 'localhost' with '127.0.0.1' in the flagged lines.${NC}" >&2
echo -e "   This forces Nginx to query explicit IPv4, avoiding intermittent IPv6 lookup drops." >&2
exit 1
