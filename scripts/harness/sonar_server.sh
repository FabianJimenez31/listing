#!/usr/bin/env bash
#
# Local SonarQube server lifecycle helper.
#   up     : start a Dockerized SonarQube, wait until ready, generate an
#            analysis token and write SONAR_HOST_URL / SONAR_TOKEN to .env.local
#   down   : stop and remove the container
#   status : print container + server status
#
# Requires: docker (daemon running), python3.
set -euo pipefail

CONTAINER="sonarqube"
IMAGE="sonarqube:lts-community"
HOST_URL="${SONAR_HOST_URL:-http://localhost:9000}"
ADMIN_DEFAULT_PW="admin"
ADMIN_NEW_PW="${SONAR_ADMIN_PASSWORD:-Sonar_Listing_2026!}"
TOKEN_NAME="local-ci"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

cmd="${1:-up}"

case "$cmd" in
  up)
    if ! docker info >/dev/null 2>&1; then
      echo -e "${RED}❌ Docker daemon is not available.${NC}"; exit 1
    fi
    sysctl -w vm.max_map_count=262144 >/dev/null 2>&1 || true

    if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER"; then
      echo -e "${YELLOW}↻ Reusing existing '$CONTAINER' container (starting if stopped).${NC}"
      docker start "$CONTAINER" >/dev/null
    else
      echo -e "${YELLOW}🐳 Starting SonarQube ($IMAGE)...${NC}"
      docker run -d --name "$CONTAINER" -p 9000:9000 \
        -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true "$IMAGE" >/dev/null
    fi

    echo -n "⏳ Waiting for SonarQube to be UP"
    for _ in $(seq 1 60); do
      status=$(python3 - "$HOST_URL" <<'PY' 2>/dev/null || true
import sys, json, urllib.request
try:
    r = urllib.request.urlopen(sys.argv[1] + "/api/system/status", timeout=4)
    print(json.load(r).get("status", ""))
except Exception:
    print("")
PY
)
      if [ "$status" = "UP" ]; then echo " ✅"; break; fi
      echo -n "."; sleep 5
    done
    if [ "${status:-}" != "UP" ]; then
      echo -e "\n${RED}❌ SonarQube did not become ready in time.${NC}"; exit 1
    fi

    echo "🔐 Provisioning admin password + analysis token..."
    TOKEN=$(python3 - "$HOST_URL" "$ADMIN_DEFAULT_PW" "$ADMIN_NEW_PW" "$TOKEN_NAME" <<'PY'
import sys, json, base64, urllib.request, urllib.parse, urllib.error
host, default_pw, new_pw, token_name = sys.argv[1:5]
def call(path, data, pw):
    req = urllib.request.Request(host + path,
        data=urllib.parse.urlencode(data).encode(), method="POST")
    req.add_header("Authorization", "Basic " + base64.b64encode(f"admin:{pw}".encode()).decode())
    try:
        r = urllib.request.urlopen(req, timeout=15); return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
# Change default password (idempotent)
st, _ = call("/api/users/change_password",
             {"login": "admin", "previousPassword": default_pw, "password": new_pw}, default_pw)
pw = new_pw
call("/api/user_tokens/revoke", {"name": token_name}, pw)
st, body = call("/api/user_tokens/generate", {"name": token_name}, pw)
print(json.loads(body)["token"])
PY
)
    {
      echo "SONAR_HOST_URL=$HOST_URL"
      echo "SONAR_TOKEN=$TOKEN"
    } > "$ROOT/.env.local"
    echo -e "${GREEN}✅ SonarQube ready at $HOST_URL${NC}"
    echo -e "${GREEN}   Token written to .env.local (admin pw: $ADMIN_NEW_PW)${NC}"
    echo -e "   Run: ${YELLOW}make sonar-check${NC}"
    ;;

  down)
    docker rm -f "$CONTAINER" >/dev/null 2>&1 && \
      echo -e "${GREEN}✅ Removed '$CONTAINER' container.${NC}" || \
      echo -e "${YELLOW}No '$CONTAINER' container to remove.${NC}"
    ;;

  status)
    docker ps -a --filter "name=$CONTAINER" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
    ;;

  *)
    echo "Usage: $0 {up|down|status}"; exit 1 ;;
esac
