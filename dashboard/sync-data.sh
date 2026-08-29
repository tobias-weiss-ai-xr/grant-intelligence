#!/usr/bin/env bash
# Sync JSON data from mcp/ to dashboard/data/
# Only catalog and sources are needed (no profile matcher on dashboard).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

mkdir -p "$SCRIPT_DIR/data"

# Catalog and sources: copy as-is
cp "$PROJECT_ROOT/mcp/catalog.json" "$SCRIPT_DIR/data/catalog.json"
cp "$PROJECT_ROOT/mcp/sources.json" "$SCRIPT_DIR/data/sources.json"

# Deadline digest (optional): only copied if present (e.g. after a CI run)
if [ -f "$PROJECT_ROOT/mcp/deadline-digest.json" ]; then
  cp "$PROJECT_ROOT/mcp/deadline-digest.json" "$SCRIPT_DIR/data/deadline-digest.json"
  DIGEST=yes
else
  DIGEST=no
fi

# Summary
CAT_COUNT=$(python3 -c "import json; print(len(json.load(open('$SCRIPT_DIR/data/catalog.json'))['programme']))")
SRC_COUNT=$(python3 -c "import json; print(len(json.load(open('$SCRIPT_DIR/data/sources.json'))))")

echo "✓ Synced data to dashboard/data/"
echo "  catalog.json: $CAT_COUNT programmes"
echo "  sources.json: $SRC_COUNT source groups"
echo "  deadline-digest.json: $DIGEST"
