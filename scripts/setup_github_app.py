#!/usr/bin/env python3
"""
GitHub App Setup Script for Holly Local Development
Cross-platform Python version that works on Windows, macOS, and Linux

This script automates the creation or detection of a GitHub App for local development.

The GitHub App requires TWO callback URLs:
1. App Installation Callback: For handling GitHub App installations on repositories
   Default: http://localhost:5173/github/app/callback
2. OAuth Callback: For handling user authentication via OAuth
   Default: http://localhost:5173/github/oauth/callback

Both URLs will be automatically configured during app creation.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import webbrowser


# Colors for terminal output (cross-platform compatible)
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

    @staticmethod
    def disable():
        """Disable colors for non-terminal output"""
        Colors.RED = ''
        Colors.GREEN = ''
        Colors.YELLOW = ''
        Colors.BLUE = ''
        Colors.CYAN = ''
        Colors.NC = ''


# Script configuration
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
KEYS_DIR = PROJECT_ROOT / ".github-app-keys"
APP_NAME_PREFIX = "holly-local-dev"

# Default URLs for local development
DEFAULT_HOMEPAGE_URL = "http://localhost:8000"
# Three callback URLs are required:
# 1. Manifest callback - handles GitHub App creation flow (receives the 'code' parameter)
DEFAULT_MANIFEST_CALLBACK_URL = "http://localhost:5173/github/app/manifest-callback"
# 2. App installation callback - handles GitHub App installations on repositories
DEFAULT_APP_CALLBACK_URL = "http://localhost:5173/github/app/callback"
# 3. OAuth callback - handles user authentication via OAuth
DEFAULT_OAUTH_CALLBACK_URL = "http://localhost:5173/github/oauth/callback"


def print_header():
    """Print script header"""
    print(f"{Colors.BLUE}╔════════════════════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.BLUE}║   Holly GitHub App Setup Script                            ║{Colors.NC}")
    print(f"{Colors.BLUE}║   Automated GitHub App Configuration for Local Dev         ║{Colors.NC}")
    print(f"{Colors.BLUE}╚════════════════════════════════════════════════════════════╝{Colors.NC}")
    print()


def run_command(cmd: list[str], capture_output: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command cross-platform"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=check,
            shell=False
        )
        return result
    except FileNotFoundError:
        return None
    except subprocess.CalledProcessError as e:
        if check:
            raise
        return e


def check_gh_cli() -> bool:
    """Check if GitHub CLI is installed"""
    if sys.platform == "win32":
        result = run_command(["gh", "--version"], check=False)
    else:
        result = run_command(["which", "gh"], check=False) or run_command(["gh", "--version"], check=False)
    
    if result is None or result.returncode != 0:
        print(f"{Colors.RED}Error: GitHub CLI (gh) is not installed{Colors.NC}")
        print("Please install it from: https://cli.github.com/")
        return False
    return True


def check_gh_auth() -> bool:
    """Check if user is authenticated with GitHub CLI"""
    result = run_command(["gh", "auth", "status"], check=False)
    if result is None or result.returncode != 0:
        print(f"{Colors.YELLOW}You are not authenticated with GitHub CLI{Colors.NC}")
        print("Please run: gh auth login")
        return False
    return True


def get_github_user() -> Optional[str]:
    """Get the authenticated GitHub user"""
    result = run_command(["gh", "api", "user", "-q", ".login"], check=False)
    if result and result.returncode == 0:
        return result.stdout.strip()
    return None


def check_existing_app() -> Optional[Dict[str, Any]]:
    """Prompt user for existing app or create new one"""
    print(f"{Colors.BLUE}Do you want to use an existing GitHub App or create a new one?{Colors.NC}")
    print()
    print(f"  {Colors.YELLOW}1){Colors.NC} Create a new GitHub App")
    print(f"  {Colors.YELLOW}2){Colors.NC} Use an existing GitHub App")
    print()

    choice = input("Enter your choice (1 or 2): ").strip()
    print()

    if choice == "2":
        print(f"{Colors.BLUE}Using an existing GitHub App{Colors.NC}")
        print()
        print(f"You can find your app details at: {Colors.YELLOW}https://github.com/settings/apps{Colors.NC}")
        print()
        print(f"{Colors.YELLOW}Note: GitHub doesn't provide an API to retrieve app details without JWT auth,{Colors.NC}")
        print(f"{Colors.YELLOW}so you'll need to manually enter the information from your app settings page.{Colors.NC}")
        print()

        app_slug = input("Enter the app slug (e.g., 'holly-local-dev-lingster-20251009'): ").strip()

        if not app_slug:
            print(f"{Colors.RED}Error: No app slug provided{Colors.NC}")
            return None

        app_id = input("Enter the App ID (from the About section): ").strip()

        if not app_id:
            print(f"{Colors.RED}Error: No App ID provided{Colors.NC}")
            return None

        app_name = input("Enter the App Name (optional, press Enter to skip): ").strip()

        if not app_name:
            app_name = app_slug

        print()
        print(f"{Colors.GREEN}✓{Colors.NC} Using app: {Colors.BLUE}{app_name}{Colors.NC} (ID: {app_id}, Slug: {app_slug})")
        print()

        # For existing apps, we need to get OAuth credentials and private key
        return {
            "id": app_id,
            "name": app_name,
            "slug": app_slug
        }
    else:
        print(f"{Colors.BLUE}Creating a new GitHub App{Colors.NC}")
        print()
        return None


def generate_app_name(github_user: str) -> str:
    """Generate a unique app name"""
    timestamp = datetime.now().strftime("%Y%m%d")
    return f"{APP_NAME_PREFIX}-{github_user}-{timestamp}"


def create_github_app(github_user: str) -> Optional[Dict[str, Any]]:
    """Create a new GitHub App using manifest flow"""
    print(f"{Colors.YELLOW}Creating new GitHub App...{Colors.NC}")
    print()
    
    # Generate unique app name
    app_name = generate_app_name(github_user)
    
    # Get URLs from user or use defaults
    homepage_url = input(f"Homepage URL (default: {DEFAULT_HOMEPAGE_URL}): ").strip() or DEFAULT_HOMEPAGE_URL
    app_callback_url = input(f"App Installation Callback URL (default: {DEFAULT_APP_CALLBACK_URL}): ").strip() or DEFAULT_APP_CALLBACK_URL
    oauth_callback_url = input(f"OAuth Callback URL (default: {DEFAULT_OAUTH_CALLBACK_URL}): ").strip() or DEFAULT_OAUTH_CALLBACK_URL
    
    print()
    print(f"{Colors.BLUE}Creating app with:{Colors.NC}")
    print(f"  Name: {Colors.YELLOW}{app_name}{Colors.NC}")
    print(f"  Homepage: {Colors.YELLOW}{homepage_url}{Colors.NC}")
    print(f"  App Callback: {Colors.YELLOW}{app_callback_url}{Colors.NC}")
    print(f"  OAuth Callback: {Colors.YELLOW}{oauth_callback_url}{Colors.NC}")
    print()
    
    # Create the app manifest
    # Manifest schema must match official GitHub documentation exactly
    # See: https://docs.github.com/en/apps/sharing-github-apps/registering-a-github-app-from-a-manifest
    # Note: webhook_active is NOT a valid key - use hook_attributes.active instead
    manifest = {
        "name": app_name,
        "url": homepage_url,
        "hook_attributes": {
            "url": "",  # Empty for local dev (no webhook endpoint)
            "active": False  # Disable webhooks for local development
        },
        "redirect_url": DEFAULT_MANIFEST_CALLBACK_URL,
        "callback_urls": [app_callback_url, oauth_callback_url],
        "setup_url": "",
        "description": "Holly - AI-powered GitHub repository analysis and code generation (Local Development)",
        "public": False,
        "default_events": [],
        "default_permissions": {
            "contents": "write",
            "metadata": "read",
            "pull_requests": "write"
        },
        "request_oauth_on_install": True
    }
    
    print(f"{Colors.BLUE}To create the app, we need to use GitHub's manifest flow.{Colors.NC}")
    print()
    print(f"{Colors.YELLOW}Please follow these steps:{Colors.NC}")
    print("1. A browser window will open to GitHub's app creation page")
    print("2. Review the permissions and settings")
    print("3. Click 'Create GitHub App'")
    print("4. You'll be redirected - copy the 'code' parameter from the URL")
    print()
    
    # Create a temporary HTML file with the manifest
    # GitHub updated manifest flow (late 2024): requires plain JSON, no HTML escaping
    # Use double quotes in HTML attribute (GitHub parses via JavaScript DOM)
    manifest_json = json.dumps(manifest, separators=(',', ':'))
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        temp_html = f.name
        # Embed raw JSON directly - GitHub's JavaScript will parse it correctly
        # Note: This requires escaping double quotes in JSON for valid HTML
        # But GitHub's parser may handle it, so we use minimal escaping
        manifest_json_escaped = manifest_json.replace('"', '&quot;')
        html_content = f"""<!DOCTYPE html>
<html>
  <body>
    <form action="https://github.com/settings/apps/new" method="post">
      <input type="hidden" name="manifest" value="{manifest_json_escaped}">
      <button>Create GitHub App</button>
    </form>
    <script>document.forms[0].submit()</script>
  </body>
</html>"""
        f.write(html_content)
    
    try:
        # Open in browser
        webbrowser.open(f"file://{temp_html}")
        print(f"{Colors.BLUE}Your browser should redirect to a URL similar to this:{Colors.NC}")
        print(f"{Colors.YELLOW}{DEFAULT_MANIFEST_CALLBACK_URL}?code=<code>{Colors.NC}")
        print()
        print(f"{Colors.GREEN}The code will be displayed in your browser with a copy button.{Colors.NC}")
        print()
        print(f"{Colors.YELLOW}You can paste either:{Colors.NC}")
        print(f"  - Just the code (e.g., 97bba380c605427d14c4e45debe14db3e4ac9f48)")
        print(f"  - The full redirect URL")
        print()
        
        user_input = input("Enter the 'code' or full redirect URL: ").strip()
        
        if not user_input:
            print(f"{Colors.RED}Error: No code provided{Colors.NC}")
            os.unlink(temp_html)
            return None
        
        # Extract code from URL if full URL was provided
        manifest_code = user_input
        if manifest_code.startswith("http://") or manifest_code.startswith("https://"):
            # Parse the URL to extract the code parameter
            parsed = urllib.parse.urlparse(manifest_code)
            # Handle both direct code parameter and nested redirect parameter
            params = urllib.parse.parse_qs(parsed.query)
            
            # Check for code in direct query params
            if "code" in params:
                manifest_code = params["code"][0]
            # Check for code in redirect parameter (URL-encoded)
            elif "redirect" in params:
                redirect_url = urllib.parse.unquote(params["redirect"][0])
                redirect_parsed = urllib.parse.urlparse(redirect_url)
                redirect_params = urllib.parse.parse_qs(redirect_parsed.query)
                if "code" in redirect_params:
                    manifest_code = redirect_params["code"][0]
        
        # Clean up the code - remove any URL-encoded prefixes (like 3D which is =)
        # GitHub codes are alphanumeric, so strip any non-alphanumeric prefixes
        manifest_code = re.sub(r'^[^a-zA-Z0-9]+', '', manifest_code)
        
        if not manifest_code:
            print(f"{Colors.RED}Error: Could not extract code from input{Colors.NC}")
            os.unlink(temp_html)
            return None
        
        print(f"{Colors.BLUE}Using code: {Colors.YELLOW}{manifest_code}{Colors.NC}")
        print()
        
        # Exchange the code for app details
        print(f"{Colors.YELLOW}Exchanging code for app details...{Colors.NC}")
        result = run_command(
            ["gh", "api", "-X", "POST", f"/app-manifests/{manifest_code}/conversions"],
            check=False
        )
        
        if not result or result.returncode != 0:
            print(f"{Colors.RED}Error: Failed to create app{Colors.NC}")
            if result:
                print(f"Error: {result.stderr}")
            os.unlink(temp_html)
            return None
        
        app_details = json.loads(result.stdout)
        
        return {
            "id": str(app_details.get("id", "")),
            "name": app_details.get("name", ""),
            "slug": app_details.get("slug", ""),
            "pem": app_details.get("pem", ""),
            "client_id": app_details.get("client_id", ""),
            "client_secret": app_details.get("client_secret", ""),
            "app_callback_url": app_callback_url,
            "oauth_callback_url": oauth_callback_url
        }
    finally:
        try:
            os.unlink(temp_html)
        except:
            pass


def download_private_key(app_slug: str) -> Optional[Path]:
    """Download or locate private key for existing app"""
    print(f"{Colors.YELLOW}Checking for existing private key...{Colors.NC}")
    
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    if sys.platform != "win32":
        os.chmod(KEYS_DIR, 0o700)
    
    private_key_path = KEYS_DIR / f"{app_slug}.pem"
    
    if private_key_path.exists():
        print(f"{Colors.GREEN}✓{Colors.NC} Found existing private key: {Colors.BLUE}{private_key_path}{Colors.NC}")
        return private_key_path
    
    print(f"{Colors.YELLOW}No private key found locally{Colors.NC}")
    print(f"{Colors.RED}Note: GitHub does not allow downloading existing private keys{Colors.NC}")
    print(f"{Colors.YELLOW}You need to generate a new private key from the GitHub App settings{Colors.NC}")
    print()
    print("Steps to generate a new private key:")
    print(f"  1. Visit: {Colors.BLUE}https://github.com/settings/apps/{app_slug}{Colors.NC}")
    print("  2. Scroll to 'Private keys'")
    print("  3. Click 'Generate a private key'")
    print("  4. Save the downloaded .pem file")
    print()
    
    user_key_path = input("Enter the path to the downloaded private key: ").strip()
    
    if not user_key_path:
        return None
    
    user_key_path = Path(user_key_path)
    if not user_key_path.exists():
        print(f"{Colors.RED}Error: File not found: {user_key_path}{Colors.NC}")
        return None
    
    # Copy the key to our keys directory
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    if sys.platform != "win32":
        os.chmod(KEYS_DIR, 0o700)
    
    import shutil
    shutil.copy2(user_key_path, private_key_path)
    
    if sys.platform != "win32":
        os.chmod(private_key_path, 0o600)
    
    print(f"{Colors.GREEN}✓{Colors.NC} Private key saved to: {Colors.BLUE}{private_key_path}{Colors.NC}")
    return private_key_path


def get_oauth_credentials(app_slug: str) -> Dict[str, str]:
    """Get OAuth credentials for existing app"""
    print()
    print(f"{Colors.YELLOW}Fetching OAuth credentials...{Colors.NC}")
    print()
    print(f"{Colors.BLUE}To get your OAuth credentials:{Colors.NC}")
    print(f"  1. Visit: {Colors.BLUE}https://github.com/settings/apps/{app_slug}{Colors.NC}")
    print("  2. Find 'Client ID' (starts with 'Iv1.')")
    print("  3. Generate a new 'Client secret' if you don't have one")
    print()
    
    client_id = input("Enter your Client ID (or press Enter to skip): ").strip()
    client_secret = ""
    
    if client_id:
        print(f"{Colors.GREEN}✓{Colors.NC} Client ID set")
        client_secret = input("Enter your Client Secret (or press Enter to skip): ").strip()
        if client_secret:
            print(f"{Colors.GREEN}✓{Colors.NC} Client Secret set")
    else:
        print(f"{Colors.YELLOW}Skipped - you'll need to add these manually later{Colors.NC}")
    
    return {"client_id": client_id, "client_secret": client_secret}


def save_private_key(pem_content: str, app_slug: str) -> Path:
    """Save private key to file"""
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    if sys.platform != "win32":
        os.chmod(KEYS_DIR, 0o700)
    
    private_key_path = KEYS_DIR / f"{app_slug}.pem"
    private_key_path.write_text(pem_content)
    
    if sys.platform != "win32":
        os.chmod(private_key_path, 0o600)
    
    print(f"{Colors.GREEN}✓{Colors.NC} Private key saved to: {Colors.BLUE}{private_key_path}{Colors.NC}")
    return private_key_path


def output_env_vars(app_id: str, app_name: str, private_key_path: Path, 
                   client_id: str = "", client_secret: str = "",
                   app_callback_url: str = DEFAULT_APP_CALLBACK_URL,
                   oauth_callback_url: str = DEFAULT_OAUTH_CALLBACK_URL):
    """Output environment variables"""
    print()
    print(f"{Colors.GREEN}╔════════════════════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.GREEN}║   GitHub App Configuration Complete!                      ║{Colors.NC}")
    print(f"{Colors.GREEN}╚════════════════════════════════════════════════════════════╝{Colors.NC}")
    print()
    print(f"{Colors.BLUE}Add these settings to your .env file:{Colors.NC}")
    print()
    print(f"{Colors.YELLOW}# GitHub App Settings{Colors.NC}")
    print(f"GITHUB_APP_ID={app_id}")
    print(f"GITHUB_APP_NAME={app_name}")
    print(f"GITHUB_APP_PRIVATE_KEY_PATH={private_key_path.as_posix()}")
    
    # Output OAuth credentials if available
    if client_id and client_id != "null":
        print()
        print(f"{Colors.YELLOW}# OAuth Settings{Colors.NC}")
        print(f"GITHUB_CLIENT_ID={client_id}")
        if client_secret and client_secret != "null":
            print(f"GITHUB_CLIENT_SECRET={client_secret}")
        else:
            print("GITHUB_CLIENT_SECRET=<generate_from_app_settings>")
    else:
        print()
        print(f"{Colors.YELLOW}# OAuth Settings - Get these from app settings{Colors.NC}")
        print("GITHUB_CLIENT_ID=<from_app_settings>")
        print("GITHUB_CLIENT_SECRET=<from_app_settings>")
    
    print()
    print(f"{Colors.YELLOW}# Configured Callback URLs{Colors.NC}")
    print(f"{Colors.GREEN}✓{Colors.NC} Manifest Callback: {Colors.BLUE}{DEFAULT_MANIFEST_CALLBACK_URL}{Colors.NC}")
    print(f"{Colors.GREEN}✓{Colors.NC} App Installation: {Colors.BLUE}{app_callback_url}{Colors.NC}")
    print(f"{Colors.GREEN}✓{Colors.NC} OAuth Callback: {Colors.BLUE}{oauth_callback_url}{Colors.NC}")
    
    # Optionally append to .env.local
    env_file = PROJECT_ROOT / ".env.local"
    if env_file.exists():
        print()
        print(f"{Colors.YELLOW}Would you like to append these settings to .env.local?{Colors.NC}")
        response = input("(y/n): ").strip().lower()
        if response == 'y':
            with open(env_file, 'a') as f:
                f.write(f"\n# GitHub App Settings (generated {datetime.now()})\n")
                f.write(f"GITHUB_APP_ID={app_id}\n")
                f.write(f"GITHUB_APP_NAME={app_name}\n")
                f.write(f"GITHUB_APP_PRIVATE_KEY_PATH={private_key_path.as_posix()}\n")
                
                if client_id and client_id != "null":
                    f.write(f"GITHUB_CLIENT_ID={client_id}\n")
                    if client_secret and client_secret != "null":
                        f.write(f"GITHUB_CLIENT_SECRET={client_secret}\n")
            
            print(f"{Colors.GREEN}✓{Colors.NC} Settings appended to .env.local")
    
    # Extract app slug from app name or URL
    app_slug = app_name.replace(f"{APP_NAME_PREFIX}-", "").split("-")[-1] if "-" in app_name else ""
    if not app_slug:
        # Try to get from existing app
        app_slug = "your-app-slug"
    
    print()
    print(f"{Colors.GREEN}Next steps:{Colors.NC}")
    print(f"  1. Copy the above settings to your {Colors.BLUE}.env{Colors.NC} or {Colors.BLUE}.env.local{Colors.NC} file")
    if not client_id or client_id == "null":
        print(f"  2. Get your OAuth credentials from: {Colors.BLUE}https://github.com/settings/apps/{app_slug}{Colors.NC}")
        print(f"  3. Verify both callback URLs are configured in the app settings")
        print(f"  4. Install the app: {Colors.BLUE}https://github.com/apps/{app_slug}/installations/new{Colors.NC}")
        print(f"  5. Run {Colors.BLUE}python manage.py runserver{Colors.NC} to test")
    else:
        print(f"  2. Verify both callback URLs are configured in the app settings")
        print(f"  3. Install the app: {Colors.BLUE}https://github.com/apps/{app_slug}/installations/new{Colors.NC}")
        print(f"  4. Run {Colors.BLUE}python manage.py runserver{Colors.NC} to test")
    print()


def main():
    """Main execution flow"""
    parser = argparse.ArgumentParser(
        description="Setup GitHub App for Holly local development"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    args = parser.parse_args()
    
    if args.no_color or not sys.stdout.isatty():
        Colors.disable()
    
    print_header()
    
    # Check prerequisites
    if not check_gh_cli():
        sys.exit(1)
    
    if not check_gh_auth():
        sys.exit(1)
    
    github_user = get_github_user()
    if not github_user:
        print(f"{Colors.RED}Error: Could not determine GitHub user{Colors.NC}")
        sys.exit(1)
    
    print(f"{Colors.GREEN}✓{Colors.NC} Authenticated as: {Colors.BLUE}{github_user}{Colors.NC}")
    print()

    # Prompt user for existing app or create new one
    existing_app = check_existing_app()

    app_id = None
    app_name = None
    app_slug = None
    private_key_path = None
    client_id = ""
    client_secret = ""
    app_callback_url = DEFAULT_APP_CALLBACK_URL
    oauth_callback_url = DEFAULT_OAUTH_CALLBACK_URL

    if existing_app:
        # Using existing app
        app_id = existing_app['id']
        app_name = existing_app['name']
        app_slug = existing_app['slug']

        private_key_path = download_private_key(app_slug)
        if not private_key_path:
            print(f"{Colors.YELLOW}Warning: No private key available{Colors.NC}")

        oauth_creds = get_oauth_credentials(app_slug)
        client_id = oauth_creds.get("client_id", "")
        client_secret = oauth_creds.get("client_secret", "")
    else:
        # Create new app
        app_details = create_github_app(github_user)
        if not app_details:
            print(f"{Colors.RED}Error: Failed to create app{Colors.NC}")
            sys.exit(1)

        app_id = app_details['id']
        app_name = app_details['name']
        app_slug = app_details['slug']
        client_id = app_details.get('client_id', '')
        client_secret = app_details.get('client_secret', '')
        app_callback_url = app_details.get('app_callback_url', DEFAULT_APP_CALLBACK_URL)
        oauth_callback_url = app_details.get('oauth_callback_url', DEFAULT_OAUTH_CALLBACK_URL)

        # Save private key
        if app_details.get('pem'):
            private_key_path = save_private_key(app_details['pem'], app_slug)
        else:
            private_key_path = download_private_key(app_slug)

    if not private_key_path:
        print(f"{Colors.RED}Error: No private key path available{Colors.NC}")
        sys.exit(1)

    # Output configuration
    output_env_vars(
        app_id=app_id,
        app_name=app_name,
        private_key_path=private_key_path,
        client_id=client_id,
        client_secret=client_secret,
        app_callback_url=app_callback_url,
        oauth_callback_url=oauth_callback_url
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.NC}")
        sys.exit(1)
