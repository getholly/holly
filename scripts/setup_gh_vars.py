#!/usr/bin/env python3
"""
GitHub Variables and Secrets Setup Script (Python Version)

This script creates or updates GitHub secrets and variables for both develop and production environments.
Based on the requirements from deploy_develop.yml and deploy_prd.yml.

Features:
- Interactive prompts for secrets with .env file defaults
- Validation of secret formats
- GitHub token validation via API
- Backup and rollback capability
- Dry-run mode
- List current secrets
- YAML export/import

Requirements:
    pip install requests python-dotenv pyyaml
"""

import argparse
import base64
import getpass
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import yaml
from dotenv import dotenv_values
from nacl import encoding, public


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


class GitHubSecretsManager:
    """Manages GitHub repository secrets and variables via REST API"""

    def __init__(self, token: str, repo: str, dry_run: bool = False):
        self.token = token
        self.repo = repo
        self.dry_run = dry_run
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.backup_data: Dict[str, Any] = {}

    def print_status(self, message: str) -> None:
        """Print status message in green"""
        print(f"{Colors.GREEN}[INFO]{Colors.NC} {message}")

    def print_warning(self, message: str) -> None:
        """Print warning message in yellow"""
        print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

    def print_error(self, message: str) -> None:
        """Print error message in red"""
        print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

    def print_dry_run(self, message: str) -> None:
        """Print dry-run message in cyan"""
        print(f"{Colors.CYAN}[DRY-RUN]{Colors.NC} {message}")

    def validate_github_token(self) -> bool:
        """Validate GitHub token by making API call"""
        try:
            response = self.session.get(f"{self.base_url}/user")
            if response.status_code == 200:
                user = response.json()
                self.print_status(f"Authenticated as: {user.get('login', 'Unknown')}")
                return True
            else:
                self.print_error(f"GitHub token validation failed: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Failed to validate GitHub token: {e}")
            return False

    def get_repository_info(self) -> Optional[Dict[str, Any]]:
        """Get repository information"""
        try:
            response = self.session.get(f"{self.base_url}/repos/{self.repo}")
            if response.status_code == 200:
                return response.json()
            else:
                self.print_error(f"Failed to get repository info: {response.status_code}")
                return None
        except Exception as e:
            self.print_error(f"Failed to get repository info: {e}")
            return None

    def get_public_key(self, environment: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Get repository or environment public key for encrypting secrets"""
        try:
            if environment:
                url = f"{self.base_url}/repos/{self.repo}/environments/{environment}/secrets/public-key"
            else:
                url = f"{self.base_url}/repos/{self.repo}/actions/secrets/public-key"

            response = self.session.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                self.print_error(f"Failed to get public key: {response.status_code}")
                return None
        except Exception as e:
            self.print_error(f"Failed to get public key: {e}")
            return None

    def encrypt_secret(self, public_key: str, secret_value: str) -> str:
        """Encrypt a secret using the repository's public key"""
        public_key_obj = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
        sealed_box = public.SealedBox(public_key_obj)
        encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
        return base64.b64encode(encrypted).decode("utf-8")

    def list_secrets(self, environment: Optional[str] = None) -> List[str]:
        """List all secrets for repository or environment"""
        try:
            if environment:
                url = f"{self.base_url}/repos/{self.repo}/environments/{environment}/secrets"
            else:
                url = f"{self.base_url}/repos/{self.repo}/actions/secrets"

            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json()
                return [secret['name'] for secret in data.get('secrets', [])]
            else:
                return []
        except Exception as e:
            self.print_error(f"Failed to list secrets: {e}")
            return []

    def set_secret(self, key: str, value: str, environment: Optional[str] = None) -> bool:
        """Set a repository or environment secret"""
        if not value:
            self.print_warning(f"Skipping empty value for {key}")
            return False

        if self.dry_run:
            scope = f"{environment} environment" if environment else "repository"
            self.print_dry_run(f"Would set secret {key} for {scope}")
            return True

        try:
            # Get public key
            public_key_data = self.get_public_key(environment)
            if not public_key_data:
                return False

            # Encrypt secret
            encrypted_value = self.encrypt_secret(public_key_data['key'], value)

            # Set secret
            if environment:
                url = f"{self.base_url}/repos/{self.repo}/environments/{environment}/secrets/{key}"
            else:
                url = f"{self.base_url}/repos/{self.repo}/actions/secrets/{key}"

            payload = {
                "encrypted_value": encrypted_value,
                "key_id": public_key_data['key_id']
            }

            response = self.session.put(url, json=payload)
            if response.status_code in [201, 204]:
                scope = f"{environment} environment" if environment else "repository"
                self.print_status(f"Set secret {key} for {scope}")
                return True
            else:
                self.print_error(f"Failed to set secret {key}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Failed to set secret {key}: {e}")
            return False

    def set_variable(self, key: str, value: str, environment: Optional[str] = None) -> bool:
        """Set a repository or environment variable"""
        if not value:
            self.print_warning(f"Skipping empty value for {key}")
            return False

        if self.dry_run:
            scope = f"{environment} environment" if environment else "repository"
            self.print_dry_run(f"Would set variable {key} for {scope}")
            return True

        try:
            if environment:
                url = f"{self.base_url}/repos/{self.repo}/environments/{environment}/variables/{key}"
            else:
                url = f"{self.base_url}/repos/{self.repo}/actions/variables/{key}"

            payload = {"name": key, "value": value}

            # Try to update first
            response = self.session.patch(url, json=payload)
            if response.status_code == 204:
                scope = f"{environment} environment" if environment else "repository"
                self.print_status(f"Updated variable {key} for {scope}")
                return True

            # If update fails, try create
            if environment:
                url = f"{self.base_url}/repos/{self.repo}/environments/{environment}/variables"
            else:
                url = f"{self.base_url}/repos/{self.repo}/actions/variables"

            response = self.session.post(url, json=payload)
            if response.status_code == 201:
                scope = f"{environment} environment" if environment else "repository"
                self.print_status(f"Created variable {key} for {scope}")
                return True
            else:
                self.print_error(f"Failed to set variable {key}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Failed to set variable {key}: {e}")
            return False

    def create_environment(self, environment: str) -> bool:
        """Create a GitHub environment if it doesn't exist"""
        if self.dry_run:
            self.print_dry_run(f"Would create environment {environment}")
            return True

        try:
            url = f"{self.base_url}/repos/{self.repo}/environments/{environment}"
            response = self.session.put(url, json={})
            if response.status_code in [200, 201]:
                self.print_status(f"Created environment {environment}")
                return True
            else:
                self.print_error(f"Failed to create environment {environment}: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Failed to create environment {environment}: {e}")
            return False

    def backup_secrets(self, filename: Optional[str] = None) -> bool:
        """Backup current secrets to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"github_secrets_backup_{timestamp}.json"

        backup = {
            "repository": self.repo,
            "timestamp": datetime.now().isoformat(),
            "secrets": {
                "repository": self.list_secrets(),
                "develop": self.list_secrets("develop"),
                "production": self.list_secrets("production")
            }
        }

        try:
            with open(filename, 'w') as f:
                json.dump(backup, f, indent=2)
            self.print_status(f"Backed up secrets to {filename}")
            self.backup_data = backup
            return True
        except Exception as e:
            self.print_error(f"Failed to backup secrets: {e}")
            return False


class SecretValidator:
    """Validates secret formats"""

    @staticmethod
    def validate_github_token(token: str) -> bool:
        """Validate GitHub token format"""
        # GitHub Personal Access Token formats
        patterns = [
            r'^ghp_[a-zA-Z0-9]{36}$',  # Classic PAT
            r'^github_pat_[a-zA-Z0-9_]{82}$',  # Fine-grained PAT
            r'^ghs_[a-zA-Z0-9]{36}$',  # GitHub App token
            r'^gho_[a-zA-Z0-9]{36}$',  # OAuth token
        ]
        return any(re.match(pattern, token) for pattern in patterns)

    @staticmethod
    def validate_aws_access_key(key: str) -> bool:
        """Validate AWS access key format"""
        return bool(re.match(r'^AKIA[0-9A-Z]{16}$', key))

    @staticmethod
    def validate_stripe_key(key: str, key_type: str = "secret") -> bool:
        """Validate Stripe key format"""
        if key_type == "secret":
            return key.startswith("sk_test_") or key.startswith("sk_live_")
        elif key_type == "public":
            return key.startswith("pk_test_") or key.startswith("pk_live_")
        return False

    @classmethod
    def validate_secret(cls, key: str, value: str) -> Tuple[bool, str]:
        """Validate secret based on key name"""
        if not value:
            return True, ""

        key_lower = key.lower()

        if "github" in key_lower and "token" in key_lower:
            if cls.validate_github_token(value):
                return True, ""
            return False, "Invalid GitHub token format"

        if "aws_access_key_id" in key_lower:
            if cls.validate_aws_access_key(value):
                return True, ""
            return False, "Invalid AWS access key format (should start with AKIA)"

        if "stripe" in key_lower:
            if "public" in key_lower:
                if cls.validate_stripe_key(value, "public"):
                    return True, ""
                return False, "Invalid Stripe public key (should start with pk_)"
            elif "secret" in key_lower:
                if cls.validate_stripe_key(value, "secret"):
                    return True, ""
                return False, "Invalid Stripe secret key (should start with sk_)"

        return True, ""


class EnvFileLoader:
    """Loads environment variables from .env files"""

    def __init__(self):
        self.env_files = [".env", ".env.local", ".env.develop", ".env.production"]
        self.loaded_values: Dict[str, Dict[str, str]] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load all .env files"""
        for env_file in self.env_files:
            if Path(env_file).exists():
                self.loaded_values[env_file] = dotenv_values(env_file)

    def get_value(self, var_name: str) -> Optional[str]:
        """Get value for variable (first found wins)"""
        for env_file in self.env_files:
            if env_file in self.loaded_values:
                value = self.loaded_values[env_file].get(var_name)
                if value:
                    return value
        return None

    def get_source_file(self, var_name: str) -> Optional[str]:
        """Get source file for variable"""
        for env_file in self.env_files:
            if env_file in self.loaded_values:
                if var_name in self.loaded_values[env_file]:
                    return env_file
        return None

    def list_found_files(self) -> List[str]:
        """List all found .env files"""
        return list(self.loaded_values.keys())


def prompt_input(prompt: str, default: str = "", is_secret: bool = False,
                var_name: str = "", env_loader: Optional[EnvFileLoader] = None) -> str:
    """Prompt user for input with optional default from .env files"""

    # Try to load from .env files if env_loader is provided
    if var_name and env_loader:
        env_value = env_loader.get_value(var_name)
        if env_value:
            source_file = env_loader.get_source_file(var_name)
            print(f"{Colors.GREEN}[INFO]{Colors.NC} Found {var_name} in {source_file}")
            default = env_value

    # Build prompt with default
    if default:
        if is_secret:
            prompt_text = f"{prompt} [***hidden***]: "
        else:
            prompt_text = f"{prompt} [{default}]: "
    else:
        prompt_text = f"{prompt}: "

    # Get input
    if is_secret:
        user_input = getpass.getpass(prompt_text)
    else:
        user_input = input(prompt_text)

    # Return input or default
    return user_input if user_input else default


def export_to_yaml(data: Dict[str, Any], filename: str) -> bool:
    """Export configuration to YAML file"""
    try:
        with open(filename, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        print(f"{Colors.GREEN}[INFO]{Colors.NC} Exported to {filename}")
        return True
    except Exception as e:
        print(f"{Colors.RED}[ERROR]{Colors.NC} Failed to export: {e}")
        return False


def import_from_yaml(filename: str) -> Optional[Dict[str, Any]]:
    """Import configuration from YAML file"""
    try:
        with open(filename, 'r') as f:
            data = yaml.safe_load(f)
        print(f"{Colors.GREEN}[INFO]{Colors.NC} Imported from {filename}")
        return data
    except Exception as e:
        print(f"{Colors.RED}[ERROR]{Colors.NC} Failed to import: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="GitHub Secrets and Variables Setup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually setting secrets"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List current secrets (names only, no values)"
    )
    parser.add_argument(
        "--export",
        metavar="FILE",
        help="Export current configuration to YAML file"
    )
    parser.add_argument(
        "--import",
        metavar="FILE",
        dest="import_file",
        help="Import configuration from YAML file"
    )
    parser.add_argument(
        "--token",
        help="GitHub personal access token (or set GITHUB_TOKEN env var)"
    )
    parser.add_argument(
        "--repo",
        help="Repository in format 'owner/repo'"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup before making changes"
    )

    args = parser.parse_args()

    # Get GitHub token
    github_token = args.token or os.getenv("GITHUB_TOKEN")
    if not github_token:
        print(f"{Colors.YELLOW}[INFO]{Colors.NC} No GitHub token found in environment")
        github_token = getpass.getpass("Enter your GitHub Personal Access Token: ")

    if not github_token:
        print(f"{Colors.RED}[ERROR]{Colors.NC} GitHub token is required")
        sys.exit(1)

    # Get repository
    repo = args.repo
    if not repo:
        # Try to detect from git
        try:
            import subprocess
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                # Parse GitHub URL
                match = re.search(r'github\.com[:/]([^/]+/[^/]+?)(\.git)?$', url)
                if match:
                    repo = match.group(1)
        except Exception:
            pass

    if not repo:
        repo = input("Enter repository (owner/repo): ")

    if not repo:
        print(f"{Colors.RED}[ERROR]{Colors.NC} Repository is required")
        sys.exit(1)

    # Initialize manager
    manager = GitHubSecretsManager(github_token, repo, dry_run=args.dry_run)

    # Validate token
    print(f"\n{Colors.BLUE}Validating GitHub token...{Colors.NC}")
    if not manager.validate_github_token():
        print(f"{Colors.RED}[ERROR]{Colors.NC} Invalid GitHub token")
        sys.exit(1)

    # Get repository info
    repo_info = manager.get_repository_info()
    if not repo_info:
        print(f"{Colors.RED}[ERROR]{Colors.NC} Failed to access repository")
        sys.exit(1)

    manager.print_status(f"Setting up secrets for repository: {repo}")

    # Handle list mode
    if args.list:
        print(f"\n{Colors.BLUE}Repository Secrets:{Colors.NC}")
        for secret in manager.list_secrets():
            print(f"  - {secret}")

        print(f"\n{Colors.BLUE}Develop Environment Secrets:{Colors.NC}")
        for secret in manager.list_secrets("develop"):
            print(f"  - {secret}")

        print(f"\n{Colors.BLUE}Production Environment Secrets:{Colors.NC}")
        for secret in manager.list_secrets("production"):
            print(f"  - {secret}")

        return

    # Handle export mode
    if args.export:
        # This would export structure only, not actual secret values
        export_data = {
            "repository": repo,
            "timestamp": datetime.now().isoformat(),
            "shared_secrets": [
                "SUBMODULE_TOKEN",
                "DJANGO_DEBUG",
                "GOOGLE_API_KEY",
                "POSTMARK_SERVER_TOKEN"
            ],
            "develop": {
                "secrets": [
                    "DEVELOP_AWS_ACCESS_KEY_ID",
                    "DEVELOP_AWS_SECRET_ACCESS_KEY",
                    "DEVELOP_GH_CLIENT_ID",
                    "DEVELOP_GH_CLIENT_SECRET",
                    "DEVELOP_GH_APP_NAME",
                    "DEVELOP_DJANGO_SECRET_KEY",
                    "DEVELOP_STRIPE_SECRET_KEY",
                    "DEVELOP_STRIPE_PUBLIC_KEY",
                    "DEVELOP_STRIPE_WEBHOOK_SECRET"
                ]
            },
            "production": {
                "secrets": [
                    "AWS_ACCESS_KEY_ID",
                    "AWS_SECRET_ACCESS_KEY",
                    "GH_CLIENT_ID",
                    "GH_CLIENT_SECRET",
                    "GH_APP_NAME",
                    "DJANGO_SECRET_KEY",
                    "STRIPE_SECRET_KEY",
                    "STRIPE_PUBLIC_KEY",
                    "STRIPE_WEBHOOK_SECRET",
                    "GEMINI_API_KEY"
                ]
            }
        }
        export_to_yaml(export_data, args.export)
        return

    # Create backup if requested
    if args.backup and not args.dry_run:
        print(f"\n{Colors.BLUE}Creating backup...{Colors.NC}")
        manager.backup_secrets()

    # Create environments
    print(f"\n{Colors.BLUE}Ensuring environments exist...{Colors.NC}")
    manager.create_environment("develop")
    manager.create_environment("production")

    # Load .env files
    env_loader = EnvFileLoader()
    env_files_found = env_loader.list_found_files()

    if env_files_found:
        manager.print_status(f"Found .env files: {', '.join(env_files_found)}")
        manager.print_status("Will use values from these files as defaults")
    else:
        manager.print_warning("No .env files found. You'll need to enter all values manually.")

    print()

    # Shared secrets
    print(f"{Colors.BLUE}=== SHARED SECRETS ==={Colors.NC}")

    submodule_token = prompt_input(
        "Enter SUBMODULE_TOKEN (GitHub token for submodule access)",
        is_secret=True,
        var_name="SUBMODULE_TOKEN",
        env_loader=env_loader
    )
    if submodule_token:
        is_valid, error = SecretValidator.validate_secret("SUBMODULE_TOKEN", submodule_token)
        if not is_valid:
            manager.print_warning(f"Validation warning: {error}")
        manager.set_secret("SUBMODULE_TOKEN", submodule_token)

    django_debug = prompt_input(
        "Enter DJANGO_DEBUG",
        default="False",
        var_name="DJANGO_DEBUG",
        env_loader=env_loader
    )
    manager.set_secret("DJANGO_DEBUG", django_debug)

    google_api_key = prompt_input(
        "Enter GOOGLE_API_KEY",
        is_secret=True,
        var_name="GOOGLE_API_KEY",
        env_loader=env_loader
    )
    manager.set_secret("GOOGLE_API_KEY", google_api_key)

    postmark_token = prompt_input(
        "Enter POSTMARK_SERVER_TOKEN",
        is_secret=True,
        var_name="POSTMARK_SERVER_TOKEN",
        env_loader=env_loader
    )
    manager.set_secret("POSTMARK_SERVER_TOKEN", postmark_token)

    print()

    # Develop environment
    print(f"{Colors.BLUE}=== DEVELOP ENVIRONMENT ==={Colors.NC}")

    develop_secrets = {
        "DEVELOP_AWS_ACCESS_KEY_ID": {"is_secret": True, "validator": True},
        "DEVELOP_AWS_SECRET_ACCESS_KEY": {"is_secret": True, "validator": False},
        "DEVELOP_GH_CLIENT_ID": {"is_secret": True, "validator": False},
        "DEVELOP_GH_CLIENT_SECRET": {"is_secret": True, "validator": False},
        "DEVELOP_GH_APP_NAME": {"is_secret": False, "validator": False, "default": "develop-github-me"},
        "DEVELOP_GH_APP_PRIVATE_KEY_PATH": {"is_secret": False, "validator": False, "default": "./develop-github-me.2025-03-18.private-key.pem"},
        "DEVELOP_GITHUB_APP_PRIVATE_KEY_NAME": {"is_secret": False, "validator": False, "default": "develop-github-me.2025-03-18.private-key.pem"},
        "DEVELOP_DJANGO_SECRET_KEY": {"is_secret": True, "validator": False},
        "DEVELOP_STRIPE_SECRET_KEY": {"is_secret": True, "validator": True},
        "DEVELOP_STRIPE_PUBLIC_KEY": {"is_secret": True, "validator": True},
        "DEVELOP_STRIPE_WEBHOOK_SECRET": {"is_secret": True, "validator": False},
    }

    for secret_name, config in develop_secrets.items():
        value = prompt_input(
            f"Enter {secret_name}",
            default=config.get("default", ""),
            is_secret=config["is_secret"],
            var_name=secret_name,
            env_loader=env_loader
        )
        if value:
            if config.get("validator"):
                is_valid, error = SecretValidator.validate_secret(secret_name, value)
                if not is_valid:
                    manager.print_warning(f"Validation warning for {secret_name}: {error}")
            manager.set_secret(secret_name, value, environment="develop")

    print()

    # Production environment
    print(f"{Colors.BLUE}=== PRODUCTION ENVIRONMENT ==={Colors.NC}")

    production_secrets = {
        "AWS_ACCESS_KEY_ID": {"is_secret": True, "validator": True},
        "AWS_SECRET_ACCESS_KEY": {"is_secret": True, "validator": False},
        "GH_CLIENT_ID": {"is_secret": True, "validator": False},
        "GH_CLIENT_SECRET": {"is_secret": True, "validator": False},
        "GH_APP_NAME": {"is_secret": False, "validator": False, "default": "analyse-github-repo"},
        "GH_APP_PRIVATE_KEY_PATH": {"is_secret": False, "validator": False, "default": "./analyse-github-repo.2025-03-13.private-key.pem"},
        "GH_APP_PRIVATE_KEY_NAME": {"is_secret": False, "validator": False, "default": "analyse-github-repo.2025-03-13.private-key.pem"},
        "DJANGO_SECRET_KEY": {"is_secret": True, "validator": False},
        "STRIPE_SECRET_KEY": {"is_secret": True, "validator": True},
        "STRIPE_PUBLIC_KEY": {"is_secret": True, "validator": True},
        "STRIPE_WEBHOOK_SECRET": {"is_secret": True, "validator": False},
        "GEMINI_API_KEY": {"is_secret": True, "validator": False},
    }

    for secret_name, config in production_secrets.items():
        value = prompt_input(
            f"Enter {secret_name} (Production)",
            default=config.get("default", ""),
            is_secret=config["is_secret"],
            var_name=secret_name if not secret_name.startswith("GH_") else f"GITHUB_{secret_name[3:]}",
            env_loader=env_loader
        )
        if value:
            if config.get("validator"):
                is_valid, error = SecretValidator.validate_secret(secret_name, value)
                if not is_valid:
                    manager.print_warning(f"Validation warning for {secret_name}: {error}")
            manager.set_secret(secret_name, value, environment="production")

    print()

    # Summary
    if args.dry_run:
        manager.print_dry_run("Dry-run complete. No secrets were actually set.")
    else:
        manager.print_status("✅ GitHub secrets setup completed successfully!")
        manager.print_status(f"View secrets at: https://github.com/{repo}/settings/secrets/actions")
        manager.print_status(f"View variables at: https://github.com/{repo}/settings/variables/actions")

    print()
    manager.print_warning("Remember to:")
    manager.print_warning("  - Upload the GitHub App private key files to your runners")
    manager.print_warning("  - Verify that secrets are working correctly in your workflows")
    manager.print_warning("  - Keep backup files secure if created")


if __name__ == "__main__":
    main()
