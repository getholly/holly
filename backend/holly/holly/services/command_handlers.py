"""
Example command handler functions.

All handlers must have signature:
    def handler(user, args: list[str], context: dict) -> str

These serve as templates for creating custom slash commands.
"""

from django.contrib.auth import get_user_model

User = get_user_model()


def summarize_conversation(user: User, args: list[str], context: dict) -> str:
    """
    Example: Summarize conversation command.

    Usage: /summarize [length]

    Args:
        user: User executing the command
        args: Command arguments (e.g., ["short"] or ["long"])
        context: Context dict with conversation_id, etc.

    Returns:
        Message to send to the AI assistant
    """
    length = args[0] if args else 'short'
    conversation_id = context.get('conversation_id', 'this conversation')

    return f"Please summarize {conversation_id} in {length} format."


def translate_text(user: User, args: list[str], context: dict) -> str:
    """
    Example: Translate text command.

    Usage: /translate <language> <text>

    Args:
        user: User executing the command
        args: [target_language, ...text_words]
        context: Context dict

    Returns:
        Message to send to the AI assistant
    """
    if len(args) < 2:
        return "Usage: /translate <language> <text>"

    target_language = args[0]
    text = ' '.join(args[1:])

    return f"Please translate the following to {target_language}: {text}"


def analyze_sentiment(user: User, args: list[str], context: dict) -> str:
    """
    Example: Analyze sentiment command.

    Usage: /sentiment

    Args:
        user: User executing the command
        args: Command arguments (optional)
        context: Context dict with conversation_id

    Returns:
        Message to send to the AI assistant
    """
    conversation_id = context.get('conversation_id', 'this conversation')

    return f"Please analyze the sentiment of {conversation_id}."
