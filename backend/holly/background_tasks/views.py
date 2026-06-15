"""
Views for handling background task status.
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .tasks import get_task_status


@login_required
@require_GET
def task_status(request, task_id):
    """
    Check the status of a background task.

    Only the user who owns the task may read its status/result.

    Args:
        request: The HTTP request
        task_id: The task ID to check

    Returns:
        JsonResponse: The task status
    """
    task_data = get_task_status(task_id)

    # Return an identical 404 whether the task is missing or owned by someone else
    # so task existence is not leaked.
    if not task_data or task_data.get("owner_id") != request.user.id:
        return JsonResponse({"error": "Task not found"}, status=404)

    return JsonResponse(task_data)
