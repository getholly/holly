# GitHub Secrets Setup Script (Python Version)

A comprehensive Python rewrite of `setup_gh_vars.sh` with enhanced features including validation, backup, dry-run mode, and more.

## Features

✨ **Enhanced Functionality**
- 🔍 **Secret Validation**: Automatic format validation for GitHub tokens, AWS keys, and Stripe keys
- 🧪 **GitHub Token Verification**: Validates tokens via GitHub API before use
- 💾 **Backup & Rollback**: Automatically backs up existing secrets before changes
- 🎯 **Dry-Run Mode**: Preview changes without actually setting secrets
- 📋 **List Secrets**: View all current secrets (names only, no values)
- 📤 **YAML Export**: Export secret configuration structure
- 📥 **.env File Loading**: Automatically loads defaults from .env files
- 🎨 **Colored Output**: Clear, readable terminal output
- 🔐 **Secure Input**: Hidden input for sensitive values

## Installation

### 1. Install Dependencies

```bash
pip install -r setup_gh_vars_requirements.txt
```

Or manually:
```bash
pip install requests python-dotenv PyYAML PyNaCl
```

### 2. Make Script Executable

```bash
chmod +x setup_gh_vars.py
```

## Prerequisites

### GitHub Personal Access Token

You need a GitHub Personal Access Token (PAT) with the following scopes:

**Required Scopes:**
- `repo` - Full control of private repositories
- `admin:org` - Full control of organizations (if setting org-level secrets)
- `workflow` - Update GitHub Action workflows

**Create a token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select the required scopes
4. Copy the token (you won't be able to see it again!)

## Usage

### Basic Usage (Interactive Mode)

```bash
# Set GITHUB_TOKEN environment variable
export GITHUB_TOKEN=ghp_your_token_here

# Run the script
python setup_gh_vars.py

# Or specify token directly
python setup_gh_vars.py --token ghp_your_token_here
```

### Dry-Run Mode (Preview Changes)

```bash
python setup_gh_vars.py --dry-run
```

This will show you what would be set without actually making any changes.

### List Current Secrets

```bash
python setup_gh_vars.py --list
```

Shows all secret names (not values) for:
- Repository secrets
- Develop environment secrets
- Production environment secrets

### Create Backup Before Changes

```bash
python setup_gh_vars.py --backup
```

Creates a timestamped JSON file with current secret names before making changes.

### Export Configuration Structure

```bash
python setup_gh_vars.py --export secrets_config.yaml
```

Exports the structure of secrets (names only) to a YAML file for documentation.

### Specify Repository

```bash
# Auto-detect from git remote
python setup_gh_vars.py

# Or specify explicitly
python setup_gh_vars.py --repo owner/repository-name
```

## Environment File Loading

The script automatically loads default values from `.env` files in this priority order:

1. `.env`
2. `.env.local`
3. `.env.develop`
4. `.env.production`

**First found value wins** - if a variable exists in multiple files, the first one found is used.

### Example .env File

```bash
# .env.develop
DEVELOP_AWS_ACCESS_KEY_ID=AKIA...
DEVELOP_AWS_SECRET_ACCESS_KEY=secret...
DEVELOP_GH_CLIENT_ID=Iv1...
DEVELOP_GH_CLIENT_SECRET=secret...
DEVELOP_DJANGO_SECRET_KEY=django-secret...
DEVELOP_STRIPE_SECRET_KEY=sk_test_...
DEVELOP_STRIPE_PUBLIC_KEY=pk_test_...
```

When prompted, the script will show:
```
[INFO] Found DEVELOP_AWS_ACCESS_KEY_ID in .env.develop
Enter DEVELOP_AWS_ACCESS_KEY_ID [***hidden***]:
```

Press Enter to use the default, or type a new value.

## Secret Validation

The script automatically validates secrets based on their names:

### GitHub Tokens
- Classic PAT: `ghp_...` (36 chars)
- Fine-grained PAT: `github_pat_...` (82 chars)
- GitHub App token: `ghs_...` (36 chars)
- OAuth token: `gho_...` (36 chars)

### AWS Credentials
- Access Key ID: `AKIA...` (20 chars)

### Stripe Keys
- Secret key: `sk_test_...` or `sk_live_...`
- Public key: `pk_test_...` or `pk_live_...`

If validation fails, you'll see a warning but can still proceed.

## Secrets Structure

### Shared Repository Secrets
- `SUBMODULE_TOKEN` - GitHub token for submodule access
- `DJANGO_DEBUG` - Django debug mode setting
- `GOOGLE_API_KEY` - Google API key
- `POSTMARK_SERVER_TOKEN` - Postmark email service token

### Develop Environment Secrets
- `DEVELOP_AWS_ACCESS_KEY_ID` - AWS access key
- `DEVELOP_AWS_SECRET_ACCESS_KEY` - AWS secret key
- `DEVELOP_GH_CLIENT_ID` - GitHub OAuth client ID
- `DEVELOP_GH_CLIENT_SECRET` - GitHub OAuth client secret
- `DEVELOP_GH_APP_NAME` - GitHub App name
- `DEVELOP_GH_APP_PRIVATE_KEY_PATH` - Path to GitHub App private key
- `DEVELOP_GITHUB_APP_PRIVATE_KEY_NAME` - GitHub App private key filename
- `DEVELOP_DJANGO_SECRET_KEY` - Django secret key
- `DEVELOP_STRIPE_SECRET_KEY` - Stripe secret key (test mode)
- `DEVELOP_STRIPE_PUBLIC_KEY` - Stripe public key (test mode)
- `DEVELOP_STRIPE_WEBHOOK_SECRET` - Stripe webhook secret

### Production Environment Secrets
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `GH_CLIENT_ID` - GitHub OAuth client ID
- `GH_CLIENT_SECRET` - GitHub OAuth client secret
- `GH_APP_NAME` - GitHub App name
- `GH_APP_PRIVATE_KEY_PATH` - Path to GitHub App private key
- `GH_APP_PRIVATE_KEY_NAME` - GitHub App private key filename
- `DJANGO_SECRET_KEY` - Django secret key
- `STRIPE_SECRET_KEY` - Stripe secret key (live mode)
- `STRIPE_PUBLIC_KEY` - Stripe public key (live mode)
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret
- `GEMINI_API_KEY` - Google Gemini API key

## Command-Line Options

```
usage: setup_gh_vars.py [-h] [--dry-run] [--list] [--export FILE]
                        [--import FILE] [--token TOKEN] [--repo REPO]
                        [--backup]

GitHub Secrets and Variables Setup Script

optional arguments:
  -h, --help       show this help message and exit
  --dry-run        Show what would be done without actually setting secrets
  --list           List current secrets (names only, no values)
  --export FILE    Export current configuration to YAML file
  --import FILE    Import configuration from YAML file
  --token TOKEN    GitHub personal access token (or set GITHUB_TOKEN env var)
  --repo REPO      Repository in format 'owner/repo'
  --backup         Create backup before making changes
```

## Security Best Practices

1. **Never commit secrets** - Add `.env*` to `.gitignore`
2. **Use environment-specific keys** - Different keys for develop/production
3. **Rotate tokens regularly** - Update tokens periodically
4. **Limit token scopes** - Only grant necessary permissions
5. **Keep backups secure** - Backup files contain secret names (not values)
6. **Use fine-grained PATs** - When possible, use fine-grained tokens with minimal permissions

## Troubleshooting

### Token Authentication Failed
```
[ERROR] GitHub token validation failed: 401
```
**Solution:** Check that your token has the required scopes (`repo`, `admin:org`, `workflow`)

### Environment Not Found
```
[ERROR] Failed to create environment develop: 404
```
**Solution:** The script should auto-create environments. Check repository permissions.

### Validation Warning
```
[WARNING] Validation warning for AWS_ACCESS_KEY_ID: Invalid AWS access key format
```
**Solution:** This is just a warning. Verify the key format is correct. You can proceed if you're certain it's valid.

### Rate Limiting
```
[ERROR] Failed to set secret: 403
```
**Solution:** GitHub API rate limits apply. Wait a few minutes and try again.

## Comparison with Bash Version

| Feature | Bash Script | Python Script |
|---------|-------------|---------------|
| Interactive prompts | ✅ | ✅ |
| .env file loading | ✅ | ✅ |
| GitHub CLI dependency | ✅ Required | ❌ Not needed |
| Secret validation | ❌ | ✅ |
| Token verification | ❌ | ✅ |
| Dry-run mode | ❌ | ✅ |
| List current secrets | ❌ | ✅ |
| Backup/rollback | ❌ | ✅ |
| YAML export | ❌ | ✅ |
| Auto-create environments | ❌ | ✅ |
| Colored output | ✅ | ✅ |
| Hidden password input | ✅ | ✅ |

## Examples

### Complete Setup with Backup

```bash
# Create backup and set all secrets
export GITHUB_TOKEN=ghp_your_token_here
python setup_gh_vars.py --backup

# Output:
# [INFO] Authenticated as: username
# [INFO] Setting up secrets for repository: owner/repo
# [INFO] Creating backup...
# [INFO] Backed up secrets to github_secrets_backup_20250324_143022.json
# [INFO] Created environment develop
# [INFO] Created environment production
# [INFO] Found .env in .env.develop
# ...
```

### Preview Changes First

```bash
# See what would be set without making changes
python setup_gh_vars.py --dry-run

# Output:
# [DRY-RUN] Would create environment develop
# [DRY-RUN] Would create environment production
# [DRY-RUN] Would set secret SUBMODULE_TOKEN for repository
# ...
```

### List Current Secrets

```bash
python setup_gh_vars.py --list

# Output:
# Repository Secrets:
#   - SUBMODULE_TOKEN
#   - DJANGO_DEBUG
#   - GOOGLE_API_KEY
#
# Develop Environment Secrets:
#   - DEVELOP_AWS_ACCESS_KEY_ID
#   - DEVELOP_GH_CLIENT_ID
# ...
```

