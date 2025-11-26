#!/bin/bash
# Script to run the tests for the Python example with coverage

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the project root directory
cd "$SCRIPT_DIR"

# Run the tests with coverage
uv run python -m pytest examples/python/tests/ -v --cov=examples/python --cov-report=term --cov-report=html:examples/python/coverage_report
