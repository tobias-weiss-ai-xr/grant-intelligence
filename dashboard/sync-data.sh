#!/usr/bin/env bash
# Sync JSON data from mcp/ to dashboard/data/
# DSGVO: Only profiles with einwilligung=true AND status="aktiv" are shipped.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

mkdir -p "$SCRIPT_DIR/data"

# Catalog and sources: copy as-is
cp "$PROJECT_ROOT/mcp/catalog.json" "$SCRIPT_DIR/data/catalog.json"
cp "$PROJECT_ROOT/mcp/sources.json" "$SCRIPT_DIR/data/sources.json"

# Profiles: DSGVO filter — only einwilligung=true AND status="aktiv"
if command -v jq &>/dev/null; then
  jq '.profile = (.profile // [] | map(select(.einwilligung == true and .status == "aktiv")))' \
    "$PROJECT_ROOT/mcp/profiles.json" > "$SCRIPT_DIR/data/profiles.json"
else
  # Python fallback (jq not available)
  python3 -c "
import json, sys
with open('$PROJECT_ROOT/mcp/profiles.json') as f:
    data = json.load(f)
profiles = data.get('profile', [])
filtered = [p for p in profiles if p.get('einwilligung') == True and p.get('status') == 'aktiv']
data['profile'] = filtered
with open('$SCRIPT_DIR/data/profiles.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
"
fi

# Summary
CAT_COUNT=$(python3 -c "import json; print(len(json.load(open('$SCRIPT_DIR/data/catalog.json'))['programme']))")
SRC_COUNT=$(python3 -c "import json; print(len(json.load(open('$SCRIPT_DIR/data/sources.json'))))")
 PROF_COUNT=$(python3 -c "import json; print(len(json.load(open('$SCRIPT_DIR/data/profiles.json')).get('profile', [])))")

echo "✓ Synced data to dashboard/data/"
echo "  catalog.json: $CAT_COUNT programmes"
echo "  sources.json: $SRC_COUNT source groups"
echo "  profiles.json: $PROF_COUNT public profiles (DSGVO-filtered)"
