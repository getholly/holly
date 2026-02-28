#!/bin/bash
set -euo pipefail

# Only run in remote Claude Code sessions
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
    exit 0
fi

echo "=== Holly session start hook ==="

# Install Rust toolchain if missing
if ! command -v cargo &>/dev/null; then
    echo "Installing Rust toolchain..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path
    source "$HOME/.cargo/env"
fi

echo "Rust: $(rustc --version)"
echo "Cargo: $(cargo --version)"

# Pre-fetch crates for holly-client (to warm the cache)
if [ -d "$CLAUDE_PROJECT_DIR/holly-client" ]; then
    echo "Pre-fetching holly-client dependencies..."
    cd "$CLAUDE_PROJECT_DIR/holly-client"
    cargo fetch 2>&1 | tail -3 || true
fi

# Pre-fetch crates for tui
if [ -d "$CLAUDE_PROJECT_DIR/tui" ]; then
    echo "Pre-fetching tui dependencies..."
    cd "$CLAUDE_PROJECT_DIR/tui"
    cargo fetch 2>&1 | tail -3 || true
fi

echo "=== Session start complete ==="
