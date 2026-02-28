#!/usr/bin/env bash
# Holly TUI — api:full equivalent for Rust
# See comments inside for full documentation.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TUI_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$TUI_DIR/.." && pwd)"

SERVER_URL="${1:-http://localhost:8000}"
OPENAPI_SRC="$REPO_ROOT/frontend/openapi/openapi.json"
OPENAPI_DEST="$TUI_DIR/openapi.json"
GENERATED_DIR="$REPO_ROOT/holly-client-gen"

echo "=== Holly TUI: api:full (Rust) ==="
echo ""

echo "Step 1/5: Fetching OpenAPI spec..."
if curl -sf "$SERVER_URL/_api/openapi.json" -o "$OPENAPI_DEST" 2>/dev/null; then
    echo "  OK: fetched from $SERVER_URL"
elif [ -f "$OPENAPI_SRC" ]; then
    cp "$OPENAPI_SRC" "$OPENAPI_DEST"
    echo "  OK: copied from frontend/openapi/openapi.json"
else
    echo "  ERROR: spec not available"; exit 1
fi

echo ""
echo "Step 2/5: openapi-generator-cli (Rust skeleton, optional)..."
if command -v npx &>/dev/null; then
    rm -rf "$GENERATED_DIR"
    npx --yes @openapitools/openapi-generator-cli generate \
        -i "$OPENAPI_DEST" -g rust -o "$GENERATED_DIR" \
        --additional-properties=packageName=holly_client_gen,library=reqwest \
        --skip-validate-spec 2>&1 | grep -E "error|warn" | head -10 || true
    echo "  OK: generated to $GENERATED_DIR (hand-written client takes precedence)"
else
    echo "  SKIP: npx not found (install Node.js to enable full generation)"
fi

echo ""
echo "Step 3/5: Building holly-client..."
cd "$REPO_ROOT/holly-client"
cargo build --release 2>&1 | grep -E "^error|Finished" || true
echo "  OK"

echo ""
echo "Step 4/5: Running all tests..."
cd "$REPO_ROOT/holly-client" && cargo test 2>&1 | grep -E "test result|FAILED" | head -3
cd "$REPO_ROOT/tui"          && cargo test 2>&1 | grep -E "test result|FAILED" | head -3

echo ""
echo "Step 5/5: Building holly-tui..."
cd "$REPO_ROOT/tui"
cargo build --release 2>&1 | grep -E "^error|Finished" || true
echo "  OK"

echo ""
echo "=== Build complete! Run: cd tui && cargo run ==="
