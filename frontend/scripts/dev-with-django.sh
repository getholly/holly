#!/bin/bash
# Script to start the Svelte dev server with Django integration

# Set environment variables for development
export VITE_DJANGO_API_URL=http://localhost:8000
export VITE_ASSETS_BASE_URL=http://localhost:8000/static
export NODE_ENV=development

# Print instructions
echo "========================================================="
echo "🚀 Starting Svelte development server with Django integration"
echo "========================================================="
echo ""
echo "This script will only start the Svelte dev server."
echo "Make sure the Django server is already running on http://localhost:8000"
echo ""
echo "For the best development experience:"
echo "1. Start the Django server first in a separate terminal with:"
echo "   cd /data/githubme && python manage.py runserver"
echo ""
echo "2. Then in another terminal, start this script to run the Svelte dev server:"
echo "   cd /data/frontend && npm run dev:django"
echo ""
echo "3. Open http://localhost:5173 in your browser to access the Svelte dev server"
echo "   The Svelte app will connect to the Django backend for API calls and authentication"
echo "========================================================="

# Run the Vite dev server
npx vite dev
