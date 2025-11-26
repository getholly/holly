from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from holly.holly.api.schemas import ErrorResponse
from holly.holly.api.user_llm_api_key_schemas import (
    UserLLMApiKeyCreateSchema,
    UserLLMApiKeySchema,
    UserLLMApiKeyUpdateSchema,
)
from holly.holly.models import LLM, UserLLMApiKey

router = Router(auth=JWTAuth())


@router.get("", response=list[UserLLMApiKeySchema])
def list_api_keys(request: HttpRequest, page: int = 1, page_size: int = 10):
    """List all API keys for the current user with pagination."""
    # Calculate offset
    offset = (page - 1) * page_size

    # Get paginated keys
    keys = UserLLMApiKey.objects.filter(user=request.user).select_related('llm').order_by('-created_at')[offset:offset + page_size]

    # Transform queryset to include masked API keys
    return [
        UserLLMApiKeySchema(
            id=key.id,
            llm_id=key.llm.id,
            llm_name=key.llm.name,
            api_key=f"**********{key.api_key[-4:]}" if key.api_key else "",
            created_at=key.created_at,
            updated_at=key.updated_at,
        )
        for key in keys
    ]


@router.post("", response={201: UserLLMApiKeySchema, 400: ErrorResponse, 404: ErrorResponse})
def create_api_key(request: HttpRequest, payload: UserLLMApiKeyCreateSchema):
    """Create a new API key for an LLM."""
    try:
        llm = LLM.objects.get(
            Q(user=request.user) | Q(is_system=True),
            id=payload.llm_id
        )
    except LLM.DoesNotExist:
        return 404, {"error": "LLM not found."}

    if UserLLMApiKey.objects.filter(user=request.user, llm=llm).exists():
        return 400, {"error": "API key for this LLM already exists."}

    api_key = UserLLMApiKey.objects.create(user=request.user, llm=llm, api_key=payload.api_key)
    return 201, UserLLMApiKeySchema(
        id=api_key.id,
        llm_id=api_key.llm.id,
        llm_name=api_key.llm.name,
        api_key=f"**********{api_key.api_key[-4:]}" if api_key.api_key else "",
        created_at=api_key.created_at,
        updated_at=api_key.updated_at,
    )


@router.put("/{api_key_id}", response={200: UserLLMApiKeySchema, 404: ErrorResponse})
def update_api_key(request: HttpRequest, api_key_id: int, payload: UserLLMApiKeyUpdateSchema):
    """Update an existing API key."""
    api_key = get_object_or_404(UserLLMApiKey, id=api_key_id, user=request.user)
    api_key.api_key = payload.api_key
    api_key.save()
    return UserLLMApiKeySchema(
        id=api_key.id,
        llm_id=api_key.llm.id,
        llm_name=api_key.llm.name,
        api_key=f"**********{api_key.api_key[-4:]}" if api_key.api_key else "",
        created_at=api_key.created_at,
        updated_at=api_key.updated_at,
    )


@router.delete("/{api_key_id}", response={204: None, 404: ErrorResponse})
def delete_api_key(request: HttpRequest, api_key_id: int):
    """Delete an API key."""
    api_key = get_object_or_404(UserLLMApiKey, id=api_key_id, user=request.user)
    api_key.delete()
    return 204, None
