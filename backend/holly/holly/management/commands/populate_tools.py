"""
Management command to populate the Tools model with predefined tool configurations.
"""

from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from loguru import logger

from holly.holly.models import Tools


class Command(BaseCommand):
    """
    Populates the Tools database with preconfigured tool configurations:
    - Shell: For executing shell commands
    - FileSystem: For file system operations
    - Browser: For web browser automation

    Each tool is configured with appropriate settings that enable them to function
    as part of the system.
    """

    help = "Populates the Tools model with predefined tool configurations"

    def add_arguments(self, parser) -> None:
        """Add command-line arguments for this command."""
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force recreation of tools even if they already exist",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the command to populate the Tools model."""
        force = options.get("force", False)

        try:
            with transaction.atomic():
                self.populate_tools(force=force)
                self.stdout.write(self.style.SUCCESS("Successfully populated Tools models"))
        except Exception as e:
            error_msg = f"Error populating Tools: {e}"
            logger.error(error_msg)
            # Create a custom exception subclass if needed for longer messages
            raise CommandError("Tools population failed") from e

    def populate_tools(self, *, force: bool = False) -> None:
        """
        Populate the database with predefined Tool configurations.

        Args:
            force: If True, recreate Tools even if they already exist
        """
        # Define the Tools and their configurations
        tool_configs = self._get_tool_configs()

        # Process each Tool configuration
        for name, config_data in tool_configs.items():
            try:
                self._create_or_update_tool(
                    name=name, description=config_data["description"], config=config_data["config"], force=force
                )
            except Exception as ex:
                logger.exception(f"Failed to populate: {name}/{ex}")

    def _create_or_update_tool(self, name: str, description: str, config: dict[str, Any], *, force: bool) -> None:
        """
        Create or update a Tool with the specified configuration.

        Args:
            name: The name of the Tool
            description: The description of the Tool
            config: The JSON configuration for the Tool
            force: If True, recreate the Tool even if it already exists
        """
        # Check if the Tool already exists
        existing_tool = Tools.objects.filter(name=name).first()

        if existing_tool and not force:
            self.stdout.write(f"Tool '{name}' already exists, skipping.")
            return

        if existing_tool and force:
            self.stdout.write(f"Updating existing Tool '{name}'.")
            existing_tool.description = description
            existing_tool.config = config
            existing_tool.save()
            return

        # Create new Tool
        Tools.objects.create(name=name, description=description, config=config)
        self.stdout.write(f"Created new Tool '{name}'.")

    def _get_tool_configs(self) -> dict[str, dict[str, Any]]:
        """
        Define and return the configurations for the Tools.

        Returns:
            A dictionary mapping Tool names to their configurations
        """
        return {
            "FileSystem": self._filesystem_tool_config(),
            "browser": self._browser_tool_config(),
            "graphiti": self._graphiti_tool_config(),
            "context7": self._context7_config(),
        }

    def _context7_config(self) -> dict[str, Any]:
        return {
            "description": "Allows LLM to retrieve latest doc's for any coding library",
            "config": {"command": "npx", "args": ["-y", "@upstash/context7-mcp"]},
        }

    def _filesystem_tool_config(self) -> dict[str, Any]:
        """Generate the configuration for the FileSystem tool."""
        return {"description": "file operations", "config": {}}

    def _browser_tool_config(self) -> dict[str, Any]:
        """Generate the configuration for the Browser tool."""
        return {
            "description": "Controls your web browser",
            "config": {
                "command": "uv",
                "args": [
                    "--directory",
                    "/home/ling/workarea/techarge-projects/playwright-plus-python-mcp",
                    "run",
                    "playwright-server",
                ],
            },
        }

    def _graphiti_tool_config(self) -> dict[str, Any]:
        return {
            "description": "graphiti tool for reading neo4j",
            "config": {
                "transport": "stdio",
                "command": "uv",
                "args": [
                    "--directory",
                    "/home/ling/workarea/imperialai/helios/mcp_server",
                    "run",
                    "/home/ling/workarea/imperialai/helios/mcp_server/graphiti_mcp_server.py",
                    "--transport",
                    "stdio",
                ],
                "env": {
                    "NEO4J_URI": "bolt://localhost:7687",
                    "NEO4J_USER": "neo4j",
                    "NEO4J_PASSWORD": "password",
                    "OPENAI_API_KEY": "sk-proj-",
                    "MODEL_NAME": "gpt-4o",
                },
            },
        }
