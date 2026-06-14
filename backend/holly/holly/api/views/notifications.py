"""Notification API endpoints."""

from django.http import HttpRequest
from loguru import logger
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from holly.holly.api.schemas import (
    MarkReadResponse,
    NotificationListResponse,
    NotificationSchema,
    UnreadCountResponse,
)
from holly.holly.models import Notification

router = Router(auth=JWTAuth())


@router.get("/", response=NotificationListResponse)
def list_notifications(
    request: HttpRequest,
    limit: int = 50,
    offset: int = 0,
    unread_only: bool = False
) -> NotificationListResponse:
    """
    List notifications for the authenticated user.

    Args:
        request: HTTP request
        limit: Maximum number of notifications to return
        offset: Number of notifications to skip
        unread_only: If True, only return unread notifications

    Returns:
        NotificationListResponse with notifications and counts
    """
    logger.info(f"Listing notifications for user: {request.user.email}")

    # Build queryset
    queryset = Notification.objects.filter(user=request.user)

    if unread_only:
        queryset = queryset.filter(read=False)

    # Get counts
    total_count = queryset.count()
    unread_count = Notification.objects.filter(user=request.user, read=False).count()

    # Apply pagination
    notifications_page = list(queryset[offset:offset + limit])

    # Convert to schemas
    notification_schemas = [
        NotificationSchema.model_validate(n) for n in notifications_page
    ]

    return NotificationListResponse(
        notifications=notification_schemas,
        total=total_count,
        unread_count=unread_count
    )


@router.get("/unread_count", response=UnreadCountResponse)
def get_unread_count(request: HttpRequest) -> UnreadCountResponse:
    """
    Get the count of unread notifications for the authenticated user.

    Args:
        request: HTTP request

    Returns:
        UnreadCountResponse with unread count
    """
    count = Notification.objects.filter(user=request.user, read=False).count()

    return UnreadCountResponse(count=count)


@router.post("/{notification_id}/read", response=MarkReadResponse)
def mark_notification_read(request: HttpRequest, notification_id: str) -> MarkReadResponse:
    """
    Mark a notification as read.

    Args:
        request: HTTP request
        notification_id: UUID of the notification

    Returns:
        MarkReadResponse with success status
    """
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.mark_as_read()

        return MarkReadResponse(
            success=True,
            message="Notification marked as read"
        )

    except Notification.DoesNotExist:
        return MarkReadResponse(
            success=False,
            message="Notification not found"
        )
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return MarkReadResponse(
            success=False,
            message="An internal error occurred"
        )


@router.post("/read_all", response=MarkReadResponse)
def mark_all_read(request: HttpRequest) -> MarkReadResponse:
    """
    Mark all notifications as read for the authenticated user.

    Args:
        request: HTTP request

    Returns:
        MarkReadResponse with success status
    """
    try:
        from django.utils import timezone

        updated_count = Notification.objects.filter(
            user=request.user,
            read=False
        ).update(
            read=True,
            read_at=timezone.now()
        )

        return MarkReadResponse(
            success=True,
            message=f"Marked {updated_count} notifications as read"
        )

    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        return MarkReadResponse(
            success=False,
            message="An internal error occurred"
        )


@router.delete("/{notification_id}", response=MarkReadResponse)
def delete_notification(request: HttpRequest, notification_id: str) -> MarkReadResponse:
    """
    Delete a notification.

    Args:
        request: HTTP request
        notification_id: UUID of the notification

    Returns:
        MarkReadResponse with success status
    """
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.delete()

        return MarkReadResponse(
            success=True,
            message="Notification deleted"
        )

    except Notification.DoesNotExist:
        return MarkReadResponse(
            success=False,
            message="Notification not found"
        )
    except Exception as e:
        logger.error(f"Error deleting notification: {e}")
        return MarkReadResponse(
            success=False,
            message="An internal error occurred"
        )
