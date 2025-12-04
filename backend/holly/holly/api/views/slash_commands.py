"""
Slash Command API Endpoints

Provides CRUD operations for slash commands following Django Ninja patterns.
"""

import logging
from uuid import UUID

from django.db.models import Q
from django.http import HttpRequest
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from holly.holly.api.schemas import (
    ErrorResponse,
    SlashCommandCreate,
    SlashCommandSchema,
    SlashCommandUpdate,
)
from holly.holly.models.slash_command import SlashCommand
from holly.holly.services.slash_command_service import CommandFunctionRegistry

logger = logging.getLogger(__name__)
router = Router(auth=JWTAuth())


# ============================================================================
# Serialization Helper
# ============================================================================

def _serialize_command(command: SlashCommand) -> SlashCommandSchema:
    """Convert SlashCommand model to schema"""
    return SlashCommandSchema(
        id=str(command.id),
        name=command.name,
        command_type=command.command_type,
        description=command.description or "",
        replacement_text=command.replacement_text or "",
        function_path=command.function_path or "",
        is_system=command.is_system,
        is_active=command.is_active,
        usage_count=command.usage_count,
        created_at=command.created_at,
        updated_at=command.updated_at,
    )


# ============================================================================
# CRUD Endpoints
# ============================================================================

@router.get("/", response=list[SlashCommandSchema])
def list_commands(
    request: HttpRequest,
    search: str = "",
    limit: int = 50,
):
    """
    List all commands accessible to the authenticated user.

    Returns user's own commands + system commands.
    Supports optional search by name or description.
    """
    queryset = SlashCommand.objects.filter(
        Q(user=request.user) | Q(is_system=True),
        is_active=True
    )

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )

    commands = list(queryset.order_by('-usage_count', 'name')[:limit])

    return [_serialize_command(cmd) for cmd in commands]


@router.get("/{command_id}", response={200: SlashCommandSchema, 404: ErrorResponse})
def get_command(request: HttpRequest, command_id: UUID):
    """
    Get a specific command by ID.

    Users can only access their own commands or system commands.
    """
    try:
        command = SlashCommand.objects.get(
            Q(user=request.user) | Q(is_system=True),
            id=command_id,
            is_active=True
        )
        return 200, _serialize_command(command)

    except SlashCommand.DoesNotExist:
        return 404, ErrorResponse(
            error="Command not found"
        )


@router.post("/", response={201: SlashCommandSchema, 400: ErrorResponse})
def create_command(request: HttpRequest, command_data: SlashCommandCreate):
    """
    Create a new slash command for the authenticated user.

    Validates:
    - Command name uniqueness for this user
    - Command type has required fields
    - Function paths are whitelisted
    """
    try:
        # Check for duplicate name
        if SlashCommand.objects.filter(user=request.user, name=command_data.name).exists():
            return 400, ErrorResponse(
                error=f"You already have a command named '/{command_data.name}'"
            )

        # Validate function path if function type
        if command_data.command_type == 'function':
            if not command_data.function_path:
                return 400, ErrorResponse(
                    error="Function commands must specify a function_path"
                )
            if not CommandFunctionRegistry.is_allowed(command_data.function_path):
                return 400, ErrorResponse(
                    error=f"Function path '{command_data.function_path}' is not whitelisted"
                )

        # Validate replacement text if replacement type
        if command_data.command_type == 'replacement':
            if not command_data.replacement_text:
                return 400, ErrorResponse(
                    error="Replacement commands must specify replacement_text"
                )

        # Create command
        command = SlashCommand.objects.create(
            user=request.user,
            name=command_data.name,
            command_type=command_data.command_type,
            description=command_data.description,
            replacement_text=command_data.replacement_text,
            function_path=command_data.function_path,
            is_active=command_data.is_active,
            is_system=False  # Users can never create system commands
        )

        logger.info(f"User {request.user.id} created command /{command.name}")
        return 201, _serialize_command(command)

    except Exception as e:
        logger.error(f"Error creating command: {e}")
        return 400, ErrorResponse(
            error=str(e)
        )


@router.put("/{command_id}", response={200: SlashCommandSchema, 400: ErrorResponse, 404: ErrorResponse})
def update_command(request: HttpRequest, command_id: UUID, command_data: SlashCommandUpdate):
    """
    Update an existing slash command.

    Users can only update their own commands (not system commands).
    """
    try:
        # Get command (user must own it)
        command = SlashCommand.objects.get(
            user=request.user,
            id=command_id
        )

        # Update fields if provided
        update_fields = []

        if command_data.name is not None:
            # Check for duplicate name (excluding current command)
            if SlashCommand.objects.filter(
                user=request.user,
                name=command_data.name
            ).exclude(id=command_id).exists():
                return 400, ErrorResponse(
                    error=f"You already have a command named '/{command_data.name}'"
                )
            command.name = command_data.name
            update_fields.append('name')

        if command_data.command_type is not None:
            command.command_type = command_data.command_type
            update_fields.append('command_type')

        if command_data.description is not None:
            command.description = command_data.description
            update_fields.append('description')

        if command_data.replacement_text is not None:
            command.replacement_text = command_data.replacement_text
            update_fields.append('replacement_text')

        if command_data.function_path is not None:
            if command_data.function_path and not CommandFunctionRegistry.is_allowed(command_data.function_path):
                return 400, ErrorResponse(
                    error=f"Function path '{command_data.function_path}' is not whitelisted"
                )
            command.function_path = command_data.function_path
            update_fields.append('function_path')

        if command_data.is_active is not None:
            command.is_active = command_data.is_active
            update_fields.append('is_active')

        if update_fields:
            update_fields.append('updated_at')
            command.save(update_fields=update_fields)

        logger.info(f"User {request.user.id} updated command /{command.name}")
        return 200, _serialize_command(command)

    except SlashCommand.DoesNotExist:
        return 404, ErrorResponse(
            error="Command not found or you don't have permission to update it"
        )
    except Exception as e:
        logger.error(f"Error updating command: {e}")
        return 400, ErrorResponse(
            error=str(e)
        )


@router.delete("/{command_id}", response={204: None, 404: ErrorResponse})
def delete_command(request: HttpRequest, command_id: UUID):
    """
    Delete (soft-delete) a slash command.

    Users can only delete their own commands (not system commands).
    """
    try:
        command = SlashCommand.objects.get(
            user=request.user,
            id=command_id
        )

        # Soft delete by setting is_active=False
        command.is_active = False
        command.save(update_fields=['is_active', 'updated_at'])

        logger.info(f"User {request.user.id} deleted command /{command.name}")
        return 204, None

    except SlashCommand.DoesNotExist:
        return 404, ErrorResponse(
            error="Command not found or you don't have permission to delete it"
        )


# ============================================================================
# Utility Endpoints
# ============================================================================

@router.get("/search", response=list[SlashCommandSchema])
def search_commands(
    request: HttpRequest,
    q: str = "",
    limit: int = 10
):
    """
    Autocomplete endpoint for frontend slash command picker.

    Returns top matching commands by name prefix, ordered by usage.
    """
    queryset = SlashCommand.objects.filter(
        Q(user=request.user) | Q(is_system=True),
        is_active=True
    )

    if q:
        queryset = queryset.filter(name__istartswith=q)

    commands = list(queryset.order_by('-usage_count', 'name')[:limit])
    return [_serialize_command(cmd) for cmd in commands]
