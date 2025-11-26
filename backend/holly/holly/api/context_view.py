from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from loguru import logger

from holly.holly.models import LLM


@ensure_csrf_cookie
def get_dev_context(request):
    """
    Provides the context data needed by the Svelte development server.
    This endpoint is only for development purposes.

    Args:
        request: The HTTP request

    Returns:
        JsonResponse with context data
    """
    logger.info("Serving context data for development")

    # Build the same context that would be passed to the template
    avatar_url = ""
    if hasattr(request.user, "socialaccount_set") and request.user.socialaccount_set.exists():
        social_account = request.user.socialaccount_set.first()
        if hasattr(social_account, "get_avatar_url"):
            avatar_url = social_account.get_avatar_url() or ""
    context = {
        "isAuthenticated": request.user.is_authenticated,
        "username": request.user.username if request.user.is_authenticated else "",
        "authToken": getattr(request.user, "auth_token", None),
        "csrfToken": request.META.get("CSRF_COOKIE", ""),
        "email": request.user.email if request.user.is_authenticated else "",
        "repo": "flappy-bird",  # Default for development
        "username": "Techarge",  # Default for development
        "url": "",  # Add default or logic as needed
        "avatarUrl": avatar_url,
    }

    # Add any other context data that might be provided in the view
    try:
        from holly.holly.views import HollyView

        view_instance = HollyView()
        view_instance.request = request
        additional_context = view_instance.get_context_data()
        # Update with any additional context from the view
        context.update({k: v for k, v in additional_context.items() if k not in ["view", "request"]})
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not get additional context from view: {e}")

    # Add available LLMs if that's part of your context
    try:
        available_llms = []
        for llm in LLM.objects.all():
            available_llms.append({"id": llm.id, "name": llm.name})
        context["available_llms"] = available_llms
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not get available LLMs: {e}")
        context["available_llms"] = []

    logger.info(f"Context data: {context}")
    return JsonResponse(context)
