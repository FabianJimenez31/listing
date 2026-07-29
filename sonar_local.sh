#!/usr/bin/env bash
# IA-Framework: Local SonarQube Quality Gate Analysis Script
# Usage: bash sonar_local.sh

set -e

# Load environment variables if available
if [ -f .env ]; then
    source .env
elif [ -f .env.local ]; then
    source .env.local
fi

# Ensure Sonar credentials are configured
SONAR_HOST_URL="${SONAR_HOST_URL:-http://localhost:9000}"
SONAR_TOKEN="${SONAR_TOKEN:-}"
PROJECT_KEY=$(grep "^sonar.projectKey=" sonar-project.properties | cut -d'=' -f2 || echo "ia-framework")

if [ -z "$SONAR_TOKEN" ]; then
    echo -e "\033[0;31m❌ ERROR: SONAR_TOKEN is not set in environment or .env.local file.\033[0m"
    echo "💡 Please obtain your analysis token and define it as SONAR_TOKEN."
    exit 1
fi

ROOT="$(pwd)"
BASE_SHA=$(git merge-base origin/main HEAD 2>/dev/null || git rev-parse origin/main 2>/dev/null || echo "initial")
HEAD_SHA=$(git rev-parse HEAD 2>/dev/null || echo "head")

echo "=== Base: ${BASE_SHA:0:7} → Head: ${HEAD_SHA:0:7} ==="

# 1. Run local test coverage (alimenta a Sonar)
echo ""
echo "🔄 [1/4] Running automated tests with coverage reporting..."
if command -v pytest >/dev/null 2>&1; then
    PYTHONPATH=. pytest --cov=src --cov-report=xml -q || true
elif [ -f "package.json" ] && grep -q "test:coverage" package.json; then
    npm run test:coverage || true
else
    echo "⚠️  No automated coverage configuration detected. Creating empty coverage.xml..."
    echo '<?xml version="1.0" ?><coverage version="1.0"></coverage>' > coverage.xml
fi

# 2. Run Sonar Scanner via Docker
echo ""
echo "🐳 [2/4] Running SonarQube Scanner via Docker container..."
docker run --rm --network host \
    -e SONAR_TOKEN="$SONAR_TOKEN" \
    -e SONAR_HOST_URL="$SONAR_HOST_URL" \
    -v "$ROOT:/usr/src" \
    sonarsource/sonar-scanner-cli \
    -Dsonar.scm.revision="$HEAD_SHA" \
    -Dsonar.projectVersion="1.0.0" \
    2>&1 | tail -n 25

# 3. Query SonarQube Quality Gate Status
echo ""
echo "📊 [3/4] Fetching Quality Gate results from SonarQube server..."
sleep 5 # Wait for SonarQube server to process background task

RESP=$(curl -sfS -u "$SONAR_TOKEN:" \
    "$SONAR_HOST_URL/api/qualitygates/project_status?projectKey=$PROJECT_KEY" || echo "failed")

if [ "$RESP" = "failed" ]; then
    echo -e "\033[0;31m❌ ERROR: Failed to retrieve Quality Gate status from SonarQube server.\033[0m"
    exit 1
fi

# Parse and print Quality Gate status
python3 - <<EOF
import json, sys
try:
    d = json.loads('''$RESP''')
    ps = d.get('projectStatus', {})
    status = ps.get('status', 'UNKNOWN')
    
    if status == 'OK':
        print(f"\033[0;32m✅ Quality Gate PASSED (Status: {status})\033[0m")
    else:
        print(f"\033[0;31m❌ Quality Gate FAILED (Status: {status})\033[0m")
        
    print("\nConditions:")
    for c in ps.get('conditions', []):
        icon = '✅' if c['status'] == 'OK' else '❌'
        print(f"  {icon} {c['metricKey']:35} actual={c.get('actualValue'):>10}  threshold={c.get('errorThreshold'):>4} op={c.get('comparator')}")
except Exception as e:
    print(f"Error parsing response: {e}")
    sys.exit(1)
EOF

# 4. Fetch details of new issues if failed
if echo "$RESP" | grep -q '"status":"ERROR"'; then
    echo ""
    echo -e "\033[1;33m=== 🔍 New Code Issues Detected ===\033[0m"
    curl -sS -u "$SONAR_TOKEN:" \
        "$SONAR_HOST_URL/api/issues/search?componentKeys=$PROJECT_KEY&sinceLeakPeriod=true&resolved=false&ps=15" | \
    python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    issues = d.get('issues', [])
    if not issues:
        print('  No new issues found.')
    for i in issues:
        comp = i.get('component', '').split(':', 1)[-1]
        line = i.get('line', '?')
        sev = i.get('severity', '')
        msg = i.get('message', '')[:100]
        print(f'  [{sev:6}] {comp}:{line} -> {msg}')
except Exception as e:
    pass
"
    echo ""
    exit 1
fi

echo -e "\033[0;32m🎉 Success! All SonarQube Quality Gates are green!\033[0m"
exit 0
