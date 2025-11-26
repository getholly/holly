#!/bin/bash

# GitHub Variables and Secrets Setup Script
# This script creates or updates GitHub secrets and variables for both develop and production environments
# Based on the requirements from deploy_develop.yml and deploy_prd.yml

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    print_error "GitHub CLI (gh) is not installed. Please install it first:"
    print_error "  https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    print_error "Not authenticated with GitHub CLI. Please run: gh auth login"
    exit 1
fi

# Get repository name
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
print_status "Setting up secrets and variables for repository: $REPO"

# Function to set environment secret
set_env_secret() {
    local env=$1
    local key=$2
    local value=$3

    if [ -z "$value" ]; then
        print_warning "Skipping empty value for $key in $env environment"
        return
    fi

    echo "$value" | gh secret set "$key" --env "$env"
    print_status "Set secret $key for $env environment"
}

# Function to set repository secret (shared across environments)
set_repo_secret() {
    local key=$1
    local value=$2

    if [ -z "$value" ]; then
        print_warning "Skipping empty value for $key"
        return
    fi

    echo "$value" | gh secret set "$key"
    print_status "Set repository secret $key"
}

# Function to set environment variable
set_env_variable() {
    local env=$1
    local key=$2
    local value=$3

    if [ -z "$value" ]; then
        print_warning "Skipping empty value for $key in $env environment"
        return
    fi

    gh variable set "$key" --body "$value" --env "$env"
    print_status "Set variable $key for $env environment"
}

# Function to load environment variable from .env files
load_env_var() {
    local var_name=$1
    local env_files=(".env" ".env.local" ".env.develop" ".env.production")

    for env_file in "${env_files[@]}"; do
        if [ -f "$env_file" ]; then
            # Use grep to find the variable and extract its value
            local value=$(grep "^${var_name}=" "$env_file" 2>/dev/null | head -1 | cut -d'=' -f2- | sed 's/^["'\'']//' | sed 's/["'\'']$//')
            if [ -n "$value" ]; then
                echo "$value"
                return
            fi
        fi
    done
    echo ""
}

# Function to prompt for input with optional default (enhanced to read from .env files)
prompt_input() {
    local prompt=$1
    local default=$2
    local is_secret=${3:-false}
    local var_name=$4

    # If variable name is provided, try to load from .env files
    if [ -n "$var_name" ]; then
        local env_value=$(load_env_var "$var_name")
        if [ -n "$env_value" ]; then
            default="$env_value"
            print_status "Found $var_name in .env file, using as default"
        fi
    fi

    if [ -n "$default" ]; then
        if [ "$is_secret" = true ]; then
            prompt="$prompt [***hidden***]"
        else
            prompt="$prompt [$default]"
        fi
    fi

    if [ "$is_secret" = true ]; then
        echo -n "$prompt: "
        read -s input
        echo
    else
        read -p "$prompt: " input
    fi

    if [ -z "$input" ] && [ -n "$default" ]; then
        echo "$default"
    else
        echo "$input"
    fi
}

# Check for existing .env files
print_status "Starting GitHub secrets and variables setup..."
env_files_found=()
for env_file in ".env" ".env.local" ".env.develop" ".env.production"; do
    if [ -f "$env_file" ]; then
        env_files_found+=("$env_file")
    fi
done

if [ ${#env_files_found[@]} -gt 0 ]; then
    print_status "Found existing .env files: ${env_files_found[*]}"
    print_status "Will use values from these files as defaults where available"
else
    print_warning "No .env files found. You'll need to enter all values manually."
fi
echo

# ====================
# SHARED SECRETS (used across environments)
# ====================
print_status "Setting up shared secrets..."

# GitHub App Token for submodules
SUBMODULE_TOKEN=$(prompt_input "Enter SUBMODULE_TOKEN (GitHub token for submodule access)" "" true "SUBMODULE_TOKEN")
if [ -n "$SUBMODULE_TOKEN" ]; then
    set_repo_secret "SUBMODULE_TOKEN" "$SUBMODULE_TOKEN"
fi

# Django Debug (shared across environments but could be different per env)
DJANGO_DEBUG=$(prompt_input "Enter DJANGO_DEBUG" "False" false "DJANGO_DEBUG")
set_repo_secret "DJANGO_DEBUG" "$DJANGO_DEBUG"

# Google API Key (shared)
GOOGLE_API_KEY=$(prompt_input "Enter GOOGLE_API_KEY" "" true "GOOGLE_API_KEY")
set_repo_secret "GOOGLE_API_KEY" "$GOOGLE_API_KEY"

# Postmark Server Token (shared)
POSTMARK_SERVER_TOKEN=$(prompt_input "Enter POSTMARK_SERVER_TOKEN" "" true "POSTMARK_SERVER_TOKEN")
set_repo_secret "POSTMARK_SERVER_TOKEN" "$POSTMARK_SERVER_TOKEN"

echo

# ====================
# DEVELOP ENVIRONMENT SECRETS
# ====================
print_status "Setting up DEVELOP environment secrets..."

# AWS Credentials
DEVELOP_AWS_ACCESS_KEY_ID=$(prompt_input "Enter DEVELOP_AWS_ACCESS_KEY_ID" "" true "DEVELOP_AWS_ACCESS_KEY_ID")
set_env_secret "develop" "DEVELOP_AWS_ACCESS_KEY_ID" "$DEVELOP_AWS_ACCESS_KEY_ID"

DEVELOP_AWS_SECRET_ACCESS_KEY=$(prompt_input "Enter DEVELOP_AWS_SECRET_ACCESS_KEY" "" true "DEVELOP_AWS_SECRET_ACCESS_KEY")
set_env_secret "develop" "DEVELOP_AWS_SECRET_ACCESS_KEY" "$DEVELOP_AWS_SECRET_ACCESS_KEY"

# GitHub OAuth App
DEVELOP_GH_CLIENT_ID=$(prompt_input "Enter DEVELOP_GH_CLIENT_ID" "" true "DEVELOP_GH_CLIENT_ID")
set_env_secret "develop" "DEVELOP_GH_CLIENT_ID" "$DEVELOP_GH_CLIENT_ID"

DEVELOP_GH_CLIENT_SECRET=$(prompt_input "Enter DEVELOP_GH_CLIENT_SECRET" "" true "DEVELOP_GH_CLIENT_SECRET")
set_env_secret "develop" "DEVELOP_GH_CLIENT_SECRET" "$DEVELOP_GH_CLIENT_SECRET"

# GitHub App
DEVELOP_GH_APP_NAME=$(prompt_input "Enter DEVELOP_GH_APP_NAME" "develop-github-me" false "DEVELOP_GH_APP_NAME")
set_env_secret "develop" "DEVELOP_GH_APP_NAME" "$DEVELOP_GH_APP_NAME"

DEVELOP_GH_APP_PRIVATE_KEY_PATH=$(prompt_input "Enter DEVELOP_GH_APP_PRIVATE_KEY_PATH" "./develop-github-me.2025-03-18.private-key.pem" false "DEVELOP_GH_APP_PRIVATE_KEY_PATH")
set_env_secret "develop" "DEVELOP_GH_APP_PRIVATE_KEY_PATH" "$DEVELOP_GH_APP_PRIVATE_KEY_PATH"

DEVELOP_GITHUB_APP_PRIVATE_KEY_NAME=$(prompt_input "Enter DEVELOP_GITHUB_APP_PRIVATE_KEY_NAME" "develop-github-me.2025-03-18.private-key.pem" false "DEVELOP_GITHUB_APP_PRIVATE_KEY_NAME")
set_env_secret "develop" "DEVELOP_GITHUB_APP_PRIVATE_KEY_NAME" "$DEVELOP_GITHUB_APP_PRIVATE_KEY_NAME"

# Django
DEVELOP_DJANGO_SECRET_KEY=$(prompt_input "Enter DEVELOP_DJANGO_SECRET_KEY" "" true "DEVELOP_DJANGO_SECRET_KEY")
set_env_secret "develop" "DEVELOP_DJANGO_SECRET_KEY" "$DEVELOP_DJANGO_SECRET_KEY"

# Stripe
DEVELOP_STRIPE_SECRET_KEY=$(prompt_input "Enter DEVELOP_STRIPE_SECRET_KEY" "" true "DEVELOP_STRIPE_SECRET_KEY")
set_env_secret "develop" "DEVELOP_STRIPE_SECRET_KEY" "$DEVELOP_STRIPE_SECRET_KEY"

DEVELOP_STRIPE_PUBLIC_KEY=$(prompt_input "Enter DEVELOP_STRIPE_PUBLIC_KEY" "" true "DEVELOP_STRIPE_PUBLIC_KEY")
set_env_secret "develop" "DEVELOP_STRIPE_PUBLIC_KEY" "$DEVELOP_STRIPE_PUBLIC_KEY"

DEVELOP_STRIPE_WEBHOOK_SECRET=$(prompt_input "Enter DEVELOP_STRIPE_WEBHOOK_SECRET" "" true "DEVELOP_STRIPE_WEBHOOK_SECRET")
set_env_secret "develop" "DEVELOP_STRIPE_WEBHOOK_SECRET" "$DEVELOP_STRIPE_WEBHOOK_SECRET"

echo

# ====================
# PRODUCTION ENVIRONMENT SECRETS
# ====================
print_status "Setting up PRODUCTION environment secrets..."

# AWS Credentials
PROD_AWS_ACCESS_KEY_ID=$(prompt_input "Enter AWS_ACCESS_KEY_ID (Production)" "" true "AWS_ACCESS_KEY_ID")
set_env_secret "production" "AWS_ACCESS_KEY_ID" "$PROD_AWS_ACCESS_KEY_ID"

PROD_AWS_SECRET_ACCESS_KEY=$(prompt_input "Enter AWS_SECRET_ACCESS_KEY (Production)" "" true "AWS_SECRET_ACCESS_KEY")
set_env_secret "production" "AWS_SECRET_ACCESS_KEY" "$PROD_AWS_SECRET_ACCESS_KEY"

# GitHub OAuth App
PROD_GH_CLIENT_ID=$(prompt_input "Enter GH_CLIENT_ID (Production)" "" true "GITHUB_CLIENT_ID")
set_env_secret "production" "GH_CLIENT_ID" "$PROD_GH_CLIENT_ID"

PROD_GH_CLIENT_SECRET=$(prompt_input "Enter GH_CLIENT_SECRET (Production)" "" true "GITHUB_CLIENT_SECRET")
set_env_secret "production" "GH_CLIENT_SECRET" "$PROD_GH_CLIENT_SECRET"

# GitHub App
PROD_GH_APP_NAME=$(prompt_input "Enter GH_APP_NAME (Production)" "analyse-github-repo" false "GITHUB_APP_NAME")
set_env_secret "production" "GH_APP_NAME" "$PROD_GH_APP_NAME"

PROD_GH_APP_PRIVATE_KEY_PATH=$(prompt_input "Enter GH_APP_PRIVATE_KEY_PATH (Production)" "./analyse-github-repo.2025-03-13.private-key.pem" false "GITHUB_APP_PRIVATE_KEY_PATH")
set_env_secret "production" "GH_APP_PRIVATE_KEY_PATH" "$PROD_GH_APP_PRIVATE_KEY_PATH"

PROD_GITHUB_APP_PRIVATE_KEY_NAME=$(prompt_input "Enter GITHUB_APP_PRIVATE_KEY_NAME (Production)" "analyse-github-repo.2025-03-13.private-key.pem" false "GITHUB_APP_PRIVATE_KEY_NAME")
set_env_secret "production" "GH_APP_PRIVATE_KEY_NAME" "$PROD_GITHUB_APP_PRIVATE_KEY_NAME"

# Also set alternative naming used in production workflow
set_env_secret "production" "GH_CLIENT_ID" "$PROD_GH_CLIENT_ID"
set_env_secret "production" "GH_CLIENT_SECRET" "$PROD_GH_CLIENT_SECRET"

# Django
PROD_DJANGO_SECRET_KEY=$(prompt_input "Enter DJANGO_SECRET_KEY (Production)" "" true "DJANGO_SECRET_KEY")
set_env_secret "production" "DJANGO_SECRET_KEY" "$PROD_DJANGO_SECRET_KEY"

# Stripe
PROD_STRIPE_SECRET_KEY=$(prompt_input "Enter STRIPE_SECRET_KEY (Production)" "" true "STRIPE_SECRET_KEY")
set_env_secret "production" "STRIPE_SECRET_KEY" "$PROD_STRIPE_SECRET_KEY"

PROD_STRIPE_PUBLIC_KEY=$(prompt_input "Enter STRIPE_PUBLIC_KEY (Production)" "" true "STRIPE_PUBLIC_KEY")
set_env_secret "production" "STRIPE_PUBLIC_KEY" "$PROD_STRIPE_PUBLIC_KEY"

PROD_STRIPE_WEBHOOK_SECRET=$(prompt_input "Enter STRIPE_WEBHOOK_SECRET (Production)" "" true "STRIPE_WEBHOOK_SECRET")
set_env_secret "production" "STRIPE_WEBHOOK_SECRET" "$PROD_STRIPE_WEBHOOK_SECRET"

# Gemini API Key (production only)
GEMINI_API_KEY=$(prompt_input "Enter GEMINI_API_KEY (Production)" "" true "GEMINI_API_KEY")
set_env_secret "production" "GEMINI_API_KEY" "$GEMINI_API_KEY"

echo
print_status "✅ GitHub secrets and variables setup completed successfully!"
print_status "You can view all secrets and variables at:"
print_status "  https://github.com/$REPO/settings/secrets/actions"
print_status "  https://github.com/$REPO/settings/variables/actions"
echo
print_warning "Remember to:"
print_warning "  - Upload the GitHub App private key files to your runners"
print_warning "  - Verify that the environments 'develop' and 'production' exist in your repository settings"
print_warning "  - Test your deployments to ensure all secrets are working correctly"
