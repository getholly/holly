# GitHub App Setup Script

This script automates the creation and configuration of a GitHub App for Holly local development.

## Prerequisites

1. **GitHub CLI (gh)** must be installed:
   ```bash
   # macOS
   brew install gh

   # Linux
   # See: https://github.com/cli/cli/blob/trunk/docs/install_linux.md

   # Windows
   # See: https://github.com/cli/cli#windows
   ```

2. **Authenticate with GitHub CLI**:
   ```bash
   gh auth login
   ```

3. **jq** for JSON processing (usually pre-installed on macOS/Linux):
   ```bash
   # macOS
   brew install jq

   # Linux
   sudo apt-get install jq  # Debian/Ubuntu
   sudo yum install jq      # RHEL/CentOS
   ```

## Usage

### Quick Start

```bash
cd /path/to/holly
./scripts/setup_github_app.sh
```

### What the Script Does

1. **Checks for existing Holly GitHub Apps**
   - Searches for apps matching the naming pattern `holly-local-dev-*`
   - Offers to reuse existing apps if found

2. **Creates a new GitHub App** (if needed)
   - Opens browser to GitHub's app creation flow
   - Uses manifest-based creation for automated setup
   - Configures required permissions:
     - **Contents**: Write (for reading/writing code)
     - **Metadata**: Read (for repository info)
     - **Pull Requests**: Write (for creating PRs)

3. **Manages private keys**
   - For new apps: Automatically saves the private key
   - For existing apps: Prompts to locate or generate new key
   - Stores keys securely in `.github-app-keys/` (gitignored)

4. **Retrieves OAuth credentials**
   - For new apps: Automatically extracts Client ID and Client Secret
   - For existing apps: Prompts you to enter them from the app settings
   - Includes them in the `.env` output for immediate use

5. **Outputs environment variables**
   - Displays complete settings ready to copy to `.env` file
   - Optionally appends to `.env.local` automatically

## Output

The script outputs settings in this format:

```bash
# GitHub App Settings
GITHUB_APP_ID=123456
GITHUB_APP_NAME=holly-local-dev-username-20251109
GITHUB_APP_PRIVATE_KEY_PATH=/path/to/holly/.github-app-keys/app-name.pem

# OAuth Settings
GITHUB_CLIENT_ID=Iv1.abc123def456
GITHUB_CLIENT_SECRET=abc123def456ghi789jkl012
```

**Note**: For new apps, all credentials (including Client ID and Client Secret) are automatically retrieved. For existing apps, you'll be prompted to enter the OAuth credentials.

## Post-Setup Steps

1. **Copy settings to your environment file**:
   ```bash
   # Add to .env.local or .env
   nano .env.local
   ```

   The script can automatically append settings to `.env.local` if you choose.

2. **Install the app on your repositories**:
   - Visit: `https://github.com/apps/YOUR_APP_SLUG/installations/new`
   - Select repositories you want Holly to access
   - Complete the installation

3. **Test the setup**:
   ```bash
   # Backend
   cd backend
   python manage.py runserver

   # Frontend (in another terminal)
   cd frontend
   npm run dev
   ```

4. **Verify the configuration**:
   ```bash
   cd backend
   python scripts/test_github_app_setup.py
   ```

## Directory Structure

```
holly/
├── scripts/
│   ├── setup_github_app.sh           # This setup script
│   └── README_GITHUB_APP_SETUP.md    # This documentation
├── .github-app-keys/                  # Private keys (gitignored)
│   └── app-slug.pem                   # Your app's private key
├── .env.local                         # Your environment config
└── backend/
    └── scripts/
        └── test_github_app_setup.py   # Test script
```

## Troubleshooting

### "gh: command not found"

Install the GitHub CLI:
```bash
brew install gh  # macOS
```

### "You are not authenticated with GitHub CLI"

Authenticate first:
```bash
gh auth login
```

### "jq: command not found"

Install jq:
```bash
brew install jq  # macOS
sudo apt-get install jq  # Linux
```

### Private key issues

If you're using an existing app but don't have the private key:

1. Visit your app settings: `https://github.com/settings/apps/YOUR_APP_SLUG`
2. Scroll to "Private keys"
3. Click "Generate a private key"
4. Download the `.pem` file
5. When the script prompts, provide the path to this file

### Permission errors

Ensure the `.github-app-keys/` directory has correct permissions:
```bash
chmod 700 .github-app-keys
chmod 600 .github-app-keys/*.pem
```

## Security Notes

1. **Private keys are sensitive**
   - Never commit `.pem` files to git
   - The `.github-app-keys/` directory is gitignored
   - Keys are stored with restrictive permissions (600)

2. **Environment files**
   - `.env.local` should never be committed
   - Use `.env.example` as a template for others

3. **App visibility**
   - Apps created by this script are private by default
   - Only install on repositories you trust

## Advanced Usage

### Custom URLs

The script prompts for:
- **Homepage URL**: Default is `http://localhost:8000`
- **Callback URL**: Default is `http://localhost:5173/github/app/callback`

You can customize these during setup for different environments.

### Multiple Apps

You can create multiple apps for different purposes:
- One for each developer
- Separate apps for different branches
- Different apps for testing vs development

Each app will have a unique name with timestamp.

### Reusing Apps

The script detects existing Holly apps and offers to reuse them:
- Saves time on re-setup
- Maintains consistent app settings
- Useful when switching machines or reinstalling

## Integration with Holly

Once configured, Holly will use the GitHub App for:

1. **Repository access**: Reading private repositories
2. **File operations**: Accessing code and documentation
3. **Pull request creation**: Creating PRs from AI-generated code
4. **OAuth authentication**: User login via GitHub

See the main documentation for more details:
- `/docs/GH_APP_SETUP.md` - Complete GitHub App flow
- `/backend/docs/github_app_integration.md` - Integration guide

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the GitHub App documentation: https://docs.github.com/en/apps
3. Verify your `.env` settings match the script output
4. Run the test script: `python backend/scripts/test_github_app_setup.py`
