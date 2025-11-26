#!/bin/bash
# Script to run mypy type checking using the uv environment

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the project root directory
cd "$SCRIPT_DIR"

# Run mypy using uv
uv run python run_mypy.py "$@"
