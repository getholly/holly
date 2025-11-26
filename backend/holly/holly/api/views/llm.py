from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from holly.holly.api.schemas import ErrorResponse, LLMCreate, LLMSchema, LLMUpdate
from holly.holly.models.llms import LLM

router = Router(auth=JWTAuth())


def _serialize_llm(llm: LLM) -> dict:
    """Serialize an LLM model instance to a dictionary matching LLMSchema."""
    return {
        "id": llm.id,
        "name": llm.name,
        "full_name": llm.full_name,
        "base_url": llm.base_url,
        "system_prompt": llm.system_prompt,
        "top_p": llm.top_p,
        "top_k": llm.top_k,
        "min_p": llm.min_p,
        "temperature": llm.temperature,
        "max_tokens": llm.max_tokens,
        "is_system": llm.is_system,
        "user_id": llm.user_id,
        "created_at": llm.created_at,
        "updated_at": llm.updated_at,
    }


@router.get("/", response=list[LLMSchema])
def list_llms(request: HttpRequest):
    """List all system LLMs and the current user's custom LLMs."""
    llms = LLM.objects.filter(Q(is_system=True) | Q(user=request.user))
    return [_serialize_llm(llm) for llm in llms]


@router.get("/{llm_id}", response={200: LLMSchema, 403: ErrorResponse, 404: ErrorResponse})
def get_llm(request: HttpRequest, llm_id: int):
    """Get a specific LLM by ID."""
    llm = get_object_or_404(LLM, id=llm_id)
    # Allow access to system LLMs or user's own LLMs
    if not llm.is_system and llm.user != request.user:
        return 403, {"error": "You don't have permission to access this LLM"}

    return 200, _serialize_llm(llm)


@router.post("/", response={201: LLMSchema, 400: ErrorResponse})
def create_llm(request: HttpRequest, llm_data: LLMCreate):
    """Create a new user-specific LLM."""
    # Check if user already has an LLM with this name
    if LLM.objects.filter(user=request.user, name=llm_data.name).exists():
        return 400, {"error": f"You already have an LLM named '{llm_data.name}'"}

    llm = LLM.objects.create(
        user=request.user,
        is_system=False,
        name=llm_data.name,
        full_name=llm_data.full_name,
        base_url=llm_data.base_url,
        system_prompt=llm_data.system_prompt or "",
        top_p=llm_data.top_p,
        top_k=llm_data.top_k,
        min_p=llm_data.min_p,
        temperature=llm_data.temperature if llm_data.temperature is not None else 0.0,
        max_tokens=llm_data.max_tokens if llm_data.max_tokens is not None else 4096,
    )

    return 201, _serialize_llm(llm)


@router.put("/{llm_id}", response={200: LLMSchema, 403: ErrorResponse, 404: ErrorResponse})
def update_llm(request: HttpRequest, llm_id: int, llm_data: LLMUpdate):
    """Update an existing user-specific LLM."""
    llm = get_object_or_404(LLM, id=llm_id)

    # Only allow updating user's own LLMs, not system LLMs
    if llm.is_system:
        return 403, {"error": "Cannot update system LLMs"}

    if llm.user != request.user:
        return 403, {"error": "You don't have permission to update this LLM"}

    # Update fields if provided
    if llm_data.name is not None:
        llm.name = llm_data.name
    if llm_data.full_name is not None:
        llm.full_name = llm_data.full_name
    if llm_data.base_url is not None:
        llm.base_url = llm_data.base_url
    if llm_data.system_prompt is not None:
        llm.system_prompt = llm_data.system_prompt
    if llm_data.top_p is not None:
        llm.top_p = llm_data.top_p
    if llm_data.top_k is not None:
        llm.top_k = llm_data.top_k
    if llm_data.min_p is not None:
        llm.min_p = llm_data.min_p
    if llm_data.temperature is not None:
        llm.temperature = llm_data.temperature
    if llm_data.max_tokens is not None:
        llm.max_tokens = llm_data.max_tokens

    llm.save()

    return 200, _serialize_llm(llm)


@router.delete("/{llm_id}", response={204: None, 403: ErrorResponse, 404: ErrorResponse})
def delete_llm(request: HttpRequest, llm_id: int):
    """Delete a user-specific LLM."""
    llm = get_object_or_404(LLM, id=llm_id)

    # Only allow deleting user's own LLMs, not system LLMs
    if llm.is_system:
        return 403, {"error": "Cannot delete system LLMs"}

    if llm.user != request.user:
        return 403, {"error": "You don't have permission to delete this LLM"}

    llm.delete()
    return 204, None
