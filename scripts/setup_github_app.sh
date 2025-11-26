#!/bin/bash

# GitHub App Setup Script for Holly Local Development
# This script automates the creation or detection of a GitHub App for local development
#
# The GitHub App requires TWO callback URLs:
# 1. App Installation Callback: For handling GitHub App installations on repositories
#    Default: http://localhost:5173/github/app/callback
# 2. OAuth Callback: For handling user authentication via OAuth
#    Default: http://localhost:5173/github/oauth/callback
#
# Both URLs will be automatically configured during app creation.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
KEYS_DIR="$PROJECT_ROOT/.github-app-keys"
APP_NAME_PREFIX="holly-local-dev"

# Default URLs for local development
DEFAULT_HOMEPAGE_URL="http://localhost:8000"
# Three callback URLs are required:
# 1. Manifest callback - handles GitHub App creation flow (receives the 'code' parameter)
DEFAULT_MANIFEST_CALLBACK_URL="http://localhost:5173/github/app/manifest-callback"
# 2. App installation callback - handles GitHub App installations on repositories
DEFAULT_APP_CALLBACK_URL="http://localhost:5173/github/app/callback"
# 3. OAuth callback - handles user authentication via OAuth
DEFAULT_OAUTH_CALLBACK_URL="http://localhost:5173/github/oauth/callback"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Holly GitHub App Setup Script                            ║${NC}"
echo -e "${BLUE}║   Automated GitHub App Configuration for Local Dev         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
    echo "Please install it from: https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated
# Temporarily unset GITHUB_TOKEN if it's invalid to allow gh CLI to use keyring auth
if [ -n "$GITHUB_TOKEN" ]; then
    SAVED_GITHUB_TOKEN="$GITHUB_TOKEN"
    unset GITHUB_TOKEN
fi

if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}You are not authenticated with GitHub CLI${NC}"
    echo "Please run: gh auth login"
    # Restore GITHUB_TOKEN if it was set
    if [ -n "$SAVED_GITHUB_TOKEN" ]; then
        export GITHUB_TOKEN="$SAVED_GITHUB_TOKEN"
    fi
    exit 1
fi

# Get the authenticated user
GITHUB_USER=$(gh api user -q .login 2>/dev/null)
if [ -z "$GITHUB_USER" ]; then
    echo -e "${RED}Error: Unable to get authenticated user${NC}"
    # Restore GITHUB_TOKEN if it was set
    if [ -n "$SAVED_GITHUB_TOKEN" ]; then
        export GITHUB_TOKEN="$SAVED_GITHUB_TOKEN"
    fi
    exit 1
fi

echo -e "${GREEN}✓${NC} Authenticated as: ${BLUE}$GITHUB_USER${NC}"
echo ""

# Restore GITHUB_TOKEN if it was set (for later use in the script if needed)
if [ -n "$SAVED_GITHUB_TOKEN" ]; then
    export GITHUB_TOKEN="$SAVED_GITHUB_TOKEN"
fi

# Function to prompt user for existing app or create new one
check_existing_app() {
    echo -e "${BLUE}Do you want to use an existing GitHub App or create a new one?${NC}"
    echo ""
    echo -e "  ${YELLOW}1)${NC} Create a new GitHub App"
    echo -e "  ${YELLOW}2)${NC} Use an existing GitHub App"
    echo ""
    read -p "Enter your choice (1 or 2): " CHOICE
    echo ""

    if [[ $CHOICE == "2" ]]; then
        echo -e "${BLUE}Using an existing GitHub App${NC}"
        echo ""
        echo -e "You can find your app details at: ${YELLOW}https://github.com/settings/apps${NC}"
        echo ""
        echo -e "${YELLOW}Note: GitHub doesn't provide an API to retrieve app details without JWT auth,${NC}"
        echo -e "${YELLOW}so you'll need to manually enter the information from your app settings page.${NC}"
        echo ""

        read -p "Enter the app slug (e.g., 'holly-local-dev-lingster-20251009'): " APP_SLUG

        if [ -z "$APP_SLUG" ]; then
            echo -e "${RED}Error: No app slug provided${NC}"
            return 1
        fi

        read -p "Enter the App ID (from the About section): " APP_ID

        if [ -z "$APP_ID" ]; then
            echo -e "${RED}Error: No App ID provided${NC}"
            return 1
        fi

        read -p "Enter the App Name (optional, press Enter to skip): " APP_NAME

        if [ -z "$APP_NAME" ]; then
            APP_NAME="$APP_SLUG"
        fi

        echo ""
        echo -e "${GREEN}✓${NC} Using app: ${BLUE}$APP_NAME${NC} (ID: $APP_ID, Slug: $APP_SLUG)"
        echo ""

        # For existing apps, we need to get OAuth credentials and private key
        return 0
    else
        echo -e "${BLUE}Creating a new GitHub App${NC}"
        echo ""
        return 1
    fi
}

# Function to generate a unique app name
generate_app_name() {
    TIMESTAMP=$(date +%Y%m%d)
    echo "${APP_NAME_PREFIX}-${GITHUB_USER}-${TIMESTAMP}"
}

# Function to create a new GitHub App
create_github_app() {
    echo -e "${YELLOW}Creating new GitHub App...${NC}"
    echo ""

    # Generate unique app name
    APP_NAME=$(generate_app_name)

    # Get URLs from user or use defaults
    read -p "Homepage URL (default: $DEFAULT_HOMEPAGE_URL): " HOMEPAGE_URL
    HOMEPAGE_URL=${HOMEPAGE_URL:-$DEFAULT_HOMEPAGE_URL}

    read -p "App Installation Callback URL (default: $DEFAULT_APP_CALLBACK_URL): " APP_CALLBACK_URL
    APP_CALLBACK_URL=${APP_CALLBACK_URL:-$DEFAULT_APP_CALLBACK_URL}

    read -p "OAuth Callback URL (default: $DEFAULT_OAUTH_CALLBACK_URL): " OAUTH_CALLBACK_URL
    OAUTH_CALLBACK_URL=${OAUTH_CALLBACK_URL:-$DEFAULT_OAUTH_CALLBACK_URL}

    echo ""
    echo -e "${BLUE}Creating app with:${NC}"
    echo -e "  Name: ${YELLOW}$APP_NAME${NC}"
    echo -e "  Homepage: ${YELLOW}$HOMEPAGE_URL${NC}"
    echo -e "  App Callback: ${YELLOW}$APP_CALLBACK_URL${NC}"
    echo -e "  OAuth Callback: ${YELLOW}$OAUTH_CALLBACK_URL${NC}"
    echo ""

    # Create the app manifest
    MANIFEST=$(cat <<EOF
{
  "name": "$APP_NAME",
  "url": "$HOMEPAGE_URL",
  "hook_attributes": {
    "url": ""
  },
  "redirect_url": "$DEFAULT_MANIFEST_CALLBACK_URL",
  "callback_urls": ["$APP_CALLBACK_URL", "$OAUTH_CALLBACK_URL"],
  "setup_url": "",
  "description": "Holly - AI-powered GitHub repository analysis and code generation (Local Development)",
  "public": false,
  "default_events": [],
  "default_permissions": {
    "contents": "write",
    "metadata": "read",
    "pull_requests": "write"
  },
  "request_oauth_on_install": true
}
EOF
)

    # Create the app using gh api
    echo -e "${YELLOW}Submitting app creation request...${NC}"

    # GitHub requires app creation through the web interface or using the manifest flow
    # We'll use the manifest flow which requires a code exchange
    MANIFEST_URL="https://github.com/settings/apps/new"

    echo -e "${BLUE}To create the app, we need to use GitHub's manifest flow.${NC}"
    echo ""
    echo -e "${YELLOW}Please follow these steps:${NC}"
    echo -e "1. A browser window will open to GitHub's app creation page"
    echo -e "2. Review the permissions and settings"
    echo -e "3. Click 'Create GitHub App'"
    echo -e "4. You'll be redirected - copy the 'code' parameter from the URL"
    echo ""

    # Create a temporary HTML file with the manifest
    TEMP_HTML=$(mktemp).html
    cat > "$TEMP_HTML" <<EOF
<!DOCTYPE html>
<html>
<head><title>Create Holly GitHub App</title></head>
<body>
  <h1>Creating Holly GitHub App</h1>
  <form action="https://github.com/settings/apps/new" method="post">
    <input type="hidden" name="manifest" value='$MANIFEST'/>
    <button type="submit">Create GitHub App</button>
  </form>
  <script>document.querySelector('form').submit();</script>
</body>
</html>
EOF

    # Open the HTML file in the default browser
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$TEMP_HTML"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "$TEMP_HTML" 2>/dev/null || echo "Please open: $TEMP_HTML"
    else
        echo "Please open: $TEMP_HTML"
    fi

    echo ""
    echo -e "${BLUE}Your browser should redirect to a URL similar to this:${NC}"
    echo -e "${YELLOW}http://localhost:5173/github/app/manifest-callback?code=<code>${NC}"
    echo ""
    echo -e "${GREEN}The code will be displayed in your browser with a copy button.${NC}"
    echo ""
    read -p "Enter the 'code' from the redirect URL: " MANIFEST_CODE

    if [ -z "$MANIFEST_CODE" ]; then
        echo -e "${RED}Error: No code provided${NC}"
        rm -f "$TEMP_HTML"
        exit 1
    fi

    # Exchange the code for app details
    echo -e "${YELLOW}Exchanging code for app details...${NC}"
    APP_DETAILS=$(gh api -X POST "/app-manifests/$MANIFEST_CODE/conversions" 2>/dev/null || echo "{}")

    rm -f "$TEMP_HTML"

    if [ -z "$APP_DETAILS" ] || [ "$APP_DETAILS" == "{}" ]; then
        echo -e "${RED}Error: Failed to create app${NC}"
        exit 1
    fi

    APP_ID=$(echo "$APP_DETAILS" | jq -r .id)
    APP_NAME=$(echo "$APP_DETAILS" | jq -r .name)
    APP_SLUG=$(echo "$APP_DETAILS" | jq -r .slug)
    PEM_CONTENT=$(echo "$APP_DETAILS" | jq -r .pem)
    CLIENT_ID=$(echo "$APP_DETAILS" | jq -r .client_id)
    CLIENT_SECRET=$(echo "$APP_DETAILS" | jq -r .client_secret)

    echo -e "${GREEN}✓${NC} Successfully created app: ${BLUE}$APP_NAME${NC} (ID: $APP_ID)"

    # Save the private key
    mkdir -p "$KEYS_DIR"
    chmod 700 "$KEYS_DIR"

    PRIVATE_KEY_PATH="$KEYS_DIR/${APP_SLUG}.pem"
    echo "$PEM_CONTENT" > "$PRIVATE_KEY_PATH"
    chmod 600 "$PRIVATE_KEY_PATH"

    echo -e "${GREEN}✓${NC} Private key saved to: ${BLUE}$PRIVATE_KEY_PATH${NC}"
}

# Function to download private key for existing app
download_private_key() {
    echo -e "${YELLOW}Checking for existing private key...${NC}"

    PRIVATE_KEY_PATH="$KEYS_DIR/${APP_SLUG}.pem"

    if [ -f "$PRIVATE_KEY_PATH" ]; then
        echo -e "${GREEN}✓${NC} Found existing private key: ${BLUE}$PRIVATE_KEY_PATH${NC}"
        return 0
    fi

    echo -e "${YELLOW}No private key found locally${NC}"
    echo -e "${RED}Note: GitHub does not allow downloading existing private keys${NC}"
    echo -e "${YELLOW}You need to generate a new private key from the GitHub App settings${NC}"
    echo ""
    echo -e "Steps to generate a new private key:"
    echo -e "  1. Visit: ${BLUE}https://github.com/settings/apps/${APP_SLUG}${NC}"
    echo -e "  2. Scroll to 'Private keys'"
    echo -e "  3. Click 'Generate a private key'"
    echo -e "  4. Save the downloaded .pem file"
    echo ""

    read -p "Enter the path to the downloaded private key: " USER_KEY_PATH

    if [ ! -f "$USER_KEY_PATH" ]; then
        echo -e "${RED}Error: File not found: $USER_KEY_PATH${NC}"
        exit 1
    fi

    # Copy the key to our keys directory
    mkdir -p "$KEYS_DIR"
    chmod 700 "$KEYS_DIR"
    cp "$USER_KEY_PATH" "$PRIVATE_KEY_PATH"
    chmod 600 "$PRIVATE_KEY_PATH"

    echo -e "${GREEN}✓${NC} Private key saved to: ${BLUE}$PRIVATE_KEY_PATH${NC}"
}

# Function to get OAuth credentials for existing app
get_oauth_credentials() {
    echo ""
    echo -e "${YELLOW}Fetching OAuth credentials...${NC}"

    # Note: GitHub API doesn't expose client_secret for security reasons
    # But we can get the client_id from the app details page

    echo -e "${BLUE}To get your OAuth credentials:${NC}"
    echo -e "  1. Visit: ${BLUE}https://github.com/settings/apps/${APP_SLUG}${NC}"
    echo -e "  2. Find 'Client ID' (starts with 'Iv1.')"
    echo -e "  3. Generate a new 'Client secret' if you don't have one"
    echo ""

    read -p "Enter your Client ID (or press Enter to skip): " USER_CLIENT_ID

    if [ -n "$USER_CLIENT_ID" ]; then
        CLIENT_ID="$USER_CLIENT_ID"
        echo -e "${GREEN}✓${NC} Client ID set"

        read -p "Enter your Client Secret (or press Enter to skip): " USER_CLIENT_SECRET
        if [ -n "$USER_CLIENT_SECRET" ]; then
            CLIENT_SECRET="$USER_CLIENT_SECRET"
            echo -e "${GREEN}✓${NC} Client Secret set"
        fi
    else
        CLIENT_ID=""
        CLIENT_SECRET=""
        echo -e "${YELLOW}Skipped - you'll need to add these manually later${NC}"
    fi
}

# Function to output environment variables
output_env_vars() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   GitHub App Configuration Complete!                      ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Add these settings to your .env file:${NC}"
    echo ""
    echo -e "${YELLOW}# GitHub App Settings${NC}"
    echo "GITHUB_APP_ID=$APP_ID"
    echo "GITHUB_APP_NAME=$APP_NAME"
    echo "GITHUB_APP_PRIVATE_KEY_PATH=$PRIVATE_KEY_PATH"

    # Output OAuth credentials if available
    if [ -n "$CLIENT_ID" ] && [ "$CLIENT_ID" != "null" ]; then
        echo ""
        echo -e "${YELLOW}# OAuth Settings${NC}"
        echo "GITHUB_CLIENT_ID=$CLIENT_ID"
        if [ -n "$CLIENT_SECRET" ] && [ "$CLIENT_SECRET" != "null" ]; then
            echo "GITHUB_CLIENT_SECRET=$CLIENT_SECRET"
        else
            echo "GITHUB_CLIENT_SECRET=<generate_from_app_settings>"
        fi
    else
        echo ""
        echo -e "${YELLOW}# OAuth Settings - Get these from app settings${NC}"
        echo "GITHUB_CLIENT_ID=<from_app_settings>"
        echo "GITHUB_CLIENT_SECRET=<from_app_settings>"
    fi

    echo ""
    echo -e "${YELLOW}# Configured Callback URLs${NC}"
    echo -e "${GREEN}✓${NC} Manifest Callback: ${BLUE}$DEFAULT_MANIFEST_CALLBACK_URL${NC}"
    echo -e "${GREEN}✓${NC} App Installation: ${BLUE}${APP_CALLBACK_URL:-$DEFAULT_APP_CALLBACK_URL}${NC}"
    echo -e "${GREEN}✓${NC} OAuth Callback: ${BLUE}${OAUTH_CALLBACK_URL:-$DEFAULT_OAUTH_CALLBACK_URL}${NC}"

    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo -e "  1. Copy the above settings to your ${BLUE}.env${NC} or ${BLUE}.env.local${NC} file"
    if [ -z "$CLIENT_ID" ] || [ "$CLIENT_ID" == "null" ]; then
        echo -e "  2. Get your OAuth credentials from: ${BLUE}https://github.com/settings/apps/${APP_SLUG}${NC}"
        echo -e "  3. Verify both callback URLs are configured in the app settings"
        echo -e "  4. Install the app: ${BLUE}https://github.com/apps/${APP_SLUG}/installations/new${NC}"
        echo -e "  5. Run ${BLUE}python manage.py runserver${NC} to test"
    else
        echo -e "  2. Verify both callback URLs are configured in the app settings"
        echo -e "  3. Install the app: ${BLUE}https://github.com/apps/${APP_SLUG}/installations/new${NC}"
        echo -e "  4. Run ${BLUE}python manage.py runserver${NC} to test"
    fi
    echo ""

    # Optionally append to .env.local
    ENV_FILE="$PROJECT_ROOT/.env.local"

    if [ -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}Would you like to append these settings to .env.local?${NC}"
        read -p "(y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "" >> "$ENV_FILE"
            echo "# GitHub App Settings (generated $(date))" >> "$ENV_FILE"
            echo "GITHUB_APP_ID=$APP_ID" >> "$ENV_FILE"
            echo "GITHUB_APP_NAME=$APP_NAME" >> "$ENV_FILE"
            echo "GITHUB_APP_PRIVATE_KEY_PATH=$PRIVATE_KEY_PATH" >> "$ENV_FILE"

            # Add OAuth credentials if available
            if [ -n "$CLIENT_ID" ] && [ "$CLIENT_ID" != "null" ]; then
                echo "GITHUB_CLIENT_ID=$CLIENT_ID" >> "$ENV_FILE"
                if [ -n "$CLIENT_SECRET" ] && [ "$CLIENT_SECRET" != "null" ]; then
                    echo "GITHUB_CLIENT_SECRET=$CLIENT_SECRET" >> "$ENV_FILE"
                fi
            fi

            echo -e "${GREEN}✓${NC} Settings appended to .env.local"
        fi
    fi
}

# Main execution flow
main() {
    if check_existing_app; then
        # Using existing app
        download_private_key
        get_oauth_credentials
    else
        # Create new app
        create_github_app
    fi

    # Output the configuration
    output_env_vars
}

# Run the script
main
