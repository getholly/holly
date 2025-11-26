"""
Management command to populate the Knowledge model with predefined knowledge items.
"""

from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from loguru import logger

from holly.holly.models import Knowledge


class Command(BaseCommand):
    """
    Populates the Knowledge database with predefined knowledge items:
    - Python: Knowledge about Python programming language
    - Django: Knowledge about Django web framework
    - Git: Knowledge about Git version control system

    Each knowledge item contains information that can be referenced by the MCP.
    """

    help = "Populates the Knowledge model with predefined knowledge items"

    def add_arguments(self, parser) -> None:
        """Add command-line arguments for this command."""
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force recreation of knowledge items even if they already exist",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the command to populate the Knowledge model."""
        force = options.get("force", False)

        try:
            with transaction.atomic():
                self.populate_knowledge(force=force)
                self.stdout.write(self.style.SUCCESS("Successfully populated Knowledge models"))
        except Exception as e:
            error_msg = f"Error populating Knowledge items: {e}"
            logger.error(error_msg)
            # Create a custom exception subclass if needed for longer messages
            raise CommandError("Knowledge population failed") from e

    def populate_knowledge(self, *, force: bool = False) -> None:
        """
        Populate the database with predefined Knowledge items.

        Args:
            force: If True, recreate Knowledge items even if they already exist
        """
        # Define the Knowledge items and their descriptions
        knowledge_configs = self._get_knowledge_configs()

        # Process each Knowledge item configuration
        for name, details in knowledge_configs.items():
            self._create_or_update_knowledge(
                name=name, description=details["description"], summary=details["summary"], force=force
            )

    def _create_or_update_knowledge(self, name: str, description: str, summary: str, *, force: bool) -> None:
        """
        Create or update a Knowledge item with the specified configuration.

        Args:
            name: The name of the Knowledge item
            description: The description of the Knowledge item
            force: If True, recreate the Knowledge item even if it already exists
        """
        # Check if the Knowledge item already exists
        existing_knowledge = Knowledge.objects.filter(name=name).first()

        if existing_knowledge and not force:
            self.stdout.write(f"Knowledge item '{name}' already exists, skipping.")
            return

        if existing_knowledge and force:
            self.stdout.write(f"Updating existing Knowledge item '{name}'.")
            existing_knowledge.description = description
            existing_knowledge.summary = summary
            existing_knowledge.save()
            return

        # Create new Knowledge item
        Knowledge.objects.create(name=name, description=description, summary=summary)
        self.stdout.write(f"Created new Knowledge item '{name}'.")

    def _get_knowledge_configs(self) -> dict[str, dict[str, str]]:
        """
        Define and return the configurations for the Knowledge items.

        Returns:
            A dictionary mapping Knowledge item names to their descriptions
        """
        return {
            "Python": self._python_knowledge_description(),
            "Django": self._django_knowledge_description(),
            "Git": self._git_knowledge_description(),
        }

    def _python_knowledge_description(self) -> dict[str, str]:
        """Generate the description for the Python knowledge item."""
        return {
            "summary": "Additional notes about python",
            "description": """"Python is a high-level, interpreted programming language known for its readability and versatility.

Key features:
- Easy to learn and read with a clean syntax
- Dynamically typed with automatic memory management
- Extensive standard library and third-party packages
- Support for multiple programming paradigms (procedural, object-oriented, functional)
- Cross-platform compatibility

Common use cases:
- Web development (with frameworks like Django, Flask)
- Data analysis and scientific computing (using NumPy, Pandas)
- Machine learning and AI (with libraries like TensorFlow, PyTorch)
- Automation and scripting
- Backend services and API development""",
        }

    def _django_knowledge_description(self) -> dict[str, str]:
        """Generate the description for the Django knowledge item."""
        return {
            "summary": "Additional notes about django",
            "description": """"Django is a high-level Python web framework that encourages rapid development and
clean, pragmatic design.

Key features:
- Follows the Model-View-Template (MVT) architectural pattern
- Built-in ORM (Object-Relational Mapping) for database interactions
- Automatic admin interface for content management
- URL routing system with regular expression support
- Template system for generating HTML dynamically
- Form handling and validation
- Built-in security features (CSRF protection, SQL injection prevention)

Components:
- Models: Define database structure and business logic
- Views: Handle HTTP requests and return responses
- Templates: Define the structure and layout of output (usually HTML)
- Forms: Handle user input and validation
- Admin: Auto-generated interface for content management
- Middleware: Process requests and responses globally
- Authentication: User management and permission systems
- Signals: Allow decoupled applications to get notified of actions""",
        }

    def _git_knowledge_description(self) -> dict[str, str]:
        """Generate the description for the Git knowledge item."""
        return {
            "summary": "additional notes about git",
            "description": """Git is a distributed version control system designed to track changes in source code
during software development.

Key features:
- Distributed architecture allowing offline work and multiple remotes
- Branching and merging capabilities for parallel development
- Staging area (index) for preparing commits
- Cryptographic integrity of history
- Speed and efficiency even with large projects

Common operations:
- init: Create a new Git repository
- clone: Copy a repository from a remote source
- add: Stage changes for commit
- commit: Record changes to the repository
- push: Upload local changes to a remote repository
- pull: Fetch and integrate changes from a remote repository
- branch: Create, list, or delete branches
- checkout: Switch branches or restore files
- merge: Combine changes from different branches
- rebase: Reapply commits on top of another base
- stash: Temporarily store modified files
- log: Show commit history
- diff: Show changes between commits or files

Best practices:
- Write clear, descriptive commit messages
- Commit early and often
- Use branches for new features or bug fixes
- Pull before pushing to avoid conflicts
- Regularly merge or rebase with the main branch
- Use .gitignore to exclude unnecessary files""",
        }
