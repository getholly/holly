"""Event channels for the Holly app."""

from __future__ import annotations

from django_eventstream import send_event


def conversation_channel(conversation_id: str) -> str:
    """Return the channel name for the given conversation."""
    return f"conversation-{conversation_id}"


def send_conversation_event(conversation_id: str, event: str, data: dict) -> None:
    """Send an event for the given conversation."""
    send_event(conversation_channel(conversation_id), event, data)
