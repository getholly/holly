from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST


@require_POST
@login_required
def mark_tour_completed(request) -> JsonResponse:
    """Mark the onboarding tour as completed for the current user."""
    user = request.user
    user.tour_completed = True
    user.save(update_fields=["tour_completed"])
    return JsonResponse({"status": "success"})
