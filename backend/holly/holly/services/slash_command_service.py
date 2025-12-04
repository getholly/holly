"""
Slash Command Service

Responsibilities:
- Parse incoming messages for slash commands
- Execute commands (replacement or function)
- Manage security and validation
- Handle errors gracefully
"""

import logging
import re
from dataclasses import dataclass, field
from importlib import import_module
from typing import Optional

from django.contrib.auth import get_user_model
from django.db.models import F, Q

from holly.holly.models.slash_command import SlashCommand

User = get_user_model()
logger = logging.getLogger(__name__)


@dataclass
class CommandParseResult:
    """Value object for parsed command"""
    is_command: bool
    command_name: Optional[str] = None
    args: list[str] = field(default_factory=list)
    original_message: str = ""


@dataclass
class CommandExecutionResult:
    """Value object for command execution result"""
    success: bool
    processed_message: str
    error_message: Optional[str] = None
    command_used: Optional[SlashCommand] = None


class CommandParser:
    """
    Single Responsibility: Parse messages for slash commands
    """

    COMMAND_PATTERN = re.compile(r'^/([a-zA-Z0-9_-]+)(?:\s+(.*))?$')

    @classmethod
    def parse(cls, message: str) -> CommandParseResult:
        """
        Parse a message to detect slash command.

        Args:
            message: Raw user message

        Returns:
            CommandParseResult with parsed data

        Examples:
            "/summarize hello world" -> CommandParseResult(
                is_command=True,
                command_name="summarize",
                args=["hello", "world"]
            )
        """
        message = message.strip()

        if not message.startswith('/'):
            return CommandParseResult(is_command=False, original_message=message)

        match = cls.COMMAND_PATTERN.match(message)
        if not match:
            # Invalid command format
            return CommandParseResult(is_command=False, original_message=message)

        command_name = match.group(1)
        args_string = match.group(2) or ""

        # Simple space-separated argument parsing
        args = args_string.split() if args_string else []

        return CommandParseResult(
            is_command=True,
            command_name=command_name,
            args=args,
            original_message=message
        )


class CommandFunctionRegistry:
    """
    Single Responsibility: Manage whitelisted command functions
    Security: Only pre-approved functions can be executed
    """

    # Whitelist of allowed function paths
    # In production, this could be loaded from settings or database
    ALLOWED_FUNCTIONS = {
        'holly.holly.services.command_handlers.summarize_conversation',
        'holly.holly.services.command_handlers.translate_text',
        'holly.holly.services.command_handlers.analyze_sentiment',
    }

    _function_cache: dict = {}

    @classmethod
    def is_allowed(cls, function_path: str) -> bool:
        """Check if function path is in whitelist"""
        return function_path in cls.ALLOWED_FUNCTIONS

    @classmethod
    def get_function(cls, function_path: str):
        """
        Safely import and return a whitelisted function.

        Args:
            function_path: Dotted path to function

        Returns:
            Callable function

        Raises:
            ValueError: If function not whitelisted or cannot be imported
        """
        if not cls.is_allowed(function_path):
            raise ValueError(f"Function '{function_path}' is not whitelisted for execution")

        # Check cache
        if function_path in cls._function_cache:
            return cls._function_cache[function_path]

        # Import function
        try:
            module_path, function_name = function_path.rsplit('.', 1)
            module = import_module(module_path)
            func = getattr(module, function_name)

            # Cache for future use
            cls._function_cache[function_path] = func
            return func

        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to import function '{function_path}': {e}")
            raise ValueError(f"Cannot load function '{function_path}'") from e


class CommandExecutor:
    """
    Single Responsibility: Execute slash commands
    """

    @classmethod
    def execute_replacement(
        cls,
        command: SlashCommand,
        args: list[str]
    ) -> CommandExecutionResult:
        """
        Execute a replacement-type command.

        Replaces {arg1}, {arg2}, etc. in template with provided args.
        Also supports {argN+} to capture all remaining arguments.
        """
        try:
            template = command.replacement_text

            # Build replacement dict
            replacements = {}
            for i, arg in enumerate(args, start=1):
                replacements[f'arg{i}'] = arg

            # Handle {argN+} pattern (all remaining args from position N)
            remaining_pattern = re.compile(r'\{arg(\d+)\+\}')
            for match in remaining_pattern.finditer(template):
                start_idx = int(match.group(1)) - 1
                remaining_args = ' '.join(args[start_idx:]) if start_idx < len(args) else ''
                replacements[f'arg{match.group(1)}+'] = remaining_args

            # Replace placeholders
            processed = template
            for key, value in replacements.items():
                processed = processed.replace(f'{{{key}}}', value)

            # Check for unreplaced placeholders (missing args)
            unreplaced = re.findall(r'\{(arg\d+)\}', processed)
            if unreplaced:
                return CommandExecutionResult(
                    success=False,
                    processed_message="",
                    error_message=f"Missing arguments: {', '.join(unreplaced)}"
                )

            return CommandExecutionResult(
                success=True,
                processed_message=processed,
                command_used=command
            )

        except Exception as e:
            logger.error(f"Error executing replacement command {command.name}: {e}")
            return CommandExecutionResult(
                success=False,
                processed_message="",
                error_message=f"Command execution failed: {str(e)}"
            )

    @classmethod
    def execute_function(
        cls,
        command: SlashCommand,
        args: list[str],
        user: User,
        context: Optional[dict] = None
    ) -> CommandExecutionResult:
        """
        Execute a function-type command.

        Args:
            command: SlashCommand instance
            args: Parsed arguments
            user: User executing the command
            context: Additional context (conversation_id, etc.)
        """
        try:
            func = CommandFunctionRegistry.get_function(command.function_path)

            # Call function with standard signature
            # All command functions should accept: (user, args, context) -> str
            result_text = func(user=user, args=args, context=context or {})

            if not isinstance(result_text, str):
                raise ValueError(f"Function must return string, got {type(result_text)}")

            return CommandExecutionResult(
                success=True,
                processed_message=result_text,
                command_used=command
            )

        except Exception as e:
            logger.error(f"Error executing function command {command.name}: {e}")
            return CommandExecutionResult(
                success=False,
                processed_message="",
                error_message=f"Command execution failed: {str(e)}"
            )


class SlashCommandService:
    """
    Facade service for slash command operations.

    Single entry point for command processing from views.
    """

    @classmethod
    async def process_message(
        cls,
        message: str,
        user: User,
        context: Optional[dict] = None
    ) -> CommandExecutionResult:
        """
        Main entry point: Parse and execute slash command if present.

        Args:
            message: Raw user message
            user: Authenticated user
            context: Additional context (conversation_id, mission_id, etc.)

        Returns:
            CommandExecutionResult
        """
        # Step 1: Parse
        parse_result = CommandParser.parse(message)

        if not parse_result.is_command:
            # Not a command, return original message
            return CommandExecutionResult(
                success=True,
                processed_message=parse_result.original_message
            )

        # Step 2: Lookup command
        try:
            command = await SlashCommand.objects.filter(
                Q(user=user, name=parse_result.command_name) |
                Q(is_system=True, name=parse_result.command_name),
                is_active=True
            ).afirst()

            if not command:
                return CommandExecutionResult(
                    success=False,
                    processed_message="",
                    error_message=f"Command '/{parse_result.command_name}' not found"
                )

        except Exception as e:
            logger.error(f"Error looking up command: {e}")
            return CommandExecutionResult(
                success=False,
                processed_message="",
                error_message="Failed to lookup command"
            )

        # Step 3: Execute based on type
        if command.command_type == 'replacement':
            result = CommandExecutor.execute_replacement(command, parse_result.args)
        elif command.command_type == 'function':
            result = CommandExecutor.execute_function(
                command, parse_result.args, user, context
            )
        else:
            return CommandExecutionResult(
                success=False,
                processed_message="",
                error_message=f"Unknown command type: {command.command_type}"
            )

        # Step 4: Update usage count if successful
        if result.success:
            await SlashCommand.objects.filter(id=command.id).aupdate(
                usage_count=F('usage_count') + 1
            )

        return result
