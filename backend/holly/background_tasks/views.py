"""
Views for handling background task status.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .tasks import get_task_status


@require_GET
def task_status(request, task_id):
    """
    Check the status of a background task.

    Args:
        request: The HTTP request
        task_id: The task ID to check

    Returns:
        JsonResponse: The task status
    """
    task_data = get_task_status(task_id)

    if not task_data:
        return JsonResponse({"error": "Task not found"}, status=404)

    return JsonResponse(task_data)
