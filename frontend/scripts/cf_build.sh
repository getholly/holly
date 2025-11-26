#!/bin/bash

# use this script to overwrite envs for different environments
# so we can run multiple backends or frontenv themes etc

export VITE_CF_BRANCH=$CF_PAGES_BRANCH

echo "building for: $CF_PAGES_BRANCH"
git lfs fetch --all

# example of how to run different settings
if [ "$CF_PAGES_BRANCH" == "main" ]; then
  #npm run production
  echo "building with openmineral theme for production(using cloudflare envs)"
  export VITE_THEME=openmineral
  npm run build
elif [ "$CF_PAGES_BRANCH" == "feature/themis" ]; then
  #npm run themis version against dev backend
  echo "building with themis theme for themis environment"
  export VITE_THEME=themis
  export VITE_SERVER=gaia-app.techarge.co.uk
  npm run build
elif [ "$CF_PAGES_BRANCH" == "staging" ]; then
  #npm run staging
  echo "building with default theme for staging environment"
  export VITE_THEME=default
  export VITE_SERVER=openmineral.techarge.co.uk
  npm run build
elif [ "$CF_PAGES_BRANCH" == "test" ]; then
  #npm run test
  echo "building test environment with default theme"
  export VITE_THEME=default
  export VITE_SERVER=gaia-app.techarge.co.uk
  npm run build
elif [ "$CF_PAGES_BRANCH" == "feature/concord" ]; then
  #npm run staging
  echo "building with concord theme in concord/dev environment"
  export VITE_THEME=concord
  export VITE_SERVER=gaia-app.techarge.co.uk
  npm run build
elif [ "$CF_PAGES_BRANCH" == "openmineral" ]; then
  #npm run staging
  echo "building with openmineral theme in staging environment"
  export VITE_THEME=openmineral
  export VITE_SERVER=openmineral.techarge.co.uk
  npm run build
else
  # Else run the dev script
  echo "building with default theme(using cloudflare envs)"
  export VITE_THEME=default
  npm run build
fi

# Upload sourcemaps to Highlight
if [ -z "$HIGHLIGHT_API_KEY" ]; then
  npx --yes @highlight-run/sourcemap-uploader upload --apiKey ${HIGHLIGHT_API_KEY} --path ./build
fi
