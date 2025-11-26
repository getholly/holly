"""
Views for the Holly App
"""

import json

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from loguru import logger

from .models.llms import LLM

# Removed HollyView class which was serving the Svelte frontend.
# class HollyView(LoginRequiredMixin, TemplateView):
#     ... (implementation removed) ...


@login_required
def get_holly_credentials(request: HttpRequest) -> JsonResponse:
    """
    Endpoint to provide authentication credentials and user info to the Holly frontend.

    Args:
        request: Django HTTP request object

    Returns:
        JSON response with user credentials and information
    """
    user = request.user

    # Get available LLMs
    available_llms = list(LLM.objects.values("id", "name"))

    # Get avatar URL if available
    avatar_url = ""
    if hasattr(user, "socialaccount_set") and user.socialaccount_set.exists():
        social_account = user.socialaccount_set.first()
        if hasattr(social_account, "get_avatar_url"):
            avatar_url = social_account.get_avatar_url() or ""

    # Return user info and authentication details needed by the frontend
    return JsonResponse(
        {
            "username": user.username,
            "email": user.email,
            "is_authenticated": user.is_authenticated,
            "csrf_token": request.META.get("CSRF_COOKIE", ""),
            "available_llms": available_llms,
            "avatarUrl": avatar_url,
        }
    )


@login_required
@csrf_protect
@require_POST
def submit_to_llm(request: HttpRequest, llm_id: int) -> JsonResponse:
    """
    Handle submission to the specified LLM.

    Args:
        request: The HTTP request
        llm_id: ID of the LLM to use

    Returns:
        JSON response with LLM output
    """
    # Get the LLM
    llm = get_object_or_404(LLM, id=llm_id)

    try:
        # Parse the request body
        data = json.loads(request.body)
        prompt = data.get("prompt", "")

        if not prompt:
            return JsonResponse({"error": "Prompt is required"}, status=400)

        # Log the request
        logger.info(f"LLM request: {prompt[:50]}... to {llm.name}")

        # In a real implementation, you would send the prompt to the LLM
        # For now, we'll just return a simulated response
        response = {
            "id": llm.id,
            "name": llm.name,
            "prompt": prompt,
            "response": f"This is a simulated response from {llm.name}. In a real implementation, this would be the output from the LLM with system prompt: {llm.system_prompt[:50]}...",
            "timestamp": "2025-05-07T21:30:00Z",
        }

        return JsonResponse(response)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in request body"}, status=400)
    except Exception as e:
        logger.error(f"Error processing LLM request: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)
