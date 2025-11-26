#!/bin/bash

set -e

# Load .env file
if [ -f .env ]; then
    export $(cat .env | sed 's/#.*//g' | xargs)
fi

# Check if VITE_DJANGO_API_URL is set
if [ -z "$VITE_DJANGO_API_URL" ]; then
    echo "Error: VITE_DJANGO_API_URL environment variable is not set"
    exit 1
fi

# Create openapi directory if it doesn't exist
mkdir -p ./openapi

URL="${VITE_DJANGO_API_URL}/_api/openapi.json"
OUTPUT_FILE="./openapi/openapi.json"

echo "Fetching OpenAPI schema from $URL"

# Download with error handling (-f flag fails silently on HTTP errors)
if ! curl -sf "$URL" -o "$OUTPUT_FILE"; then
    echo "Error: Failed to download OpenAPI schema from $URL"
    exit 1
fi

# Verify the file is valid JSON
if ! python3 -m json.tool "$OUTPUT_FILE" > /dev/null 2>&1; then
    echo "Error: Downloaded file is not valid JSON"
    exit 1
fi

echo "OpenAPI spec downloaded successfully from $URL"
echo "Now run: npm run api:fetch && npm run api:install"
