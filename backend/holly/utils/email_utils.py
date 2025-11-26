"""Email utility functions for the GithubMe application."""

from __future__ import annotations

from typing import Any, Union, cast

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string

# Setup logger
from loguru import logger

# Type aliases
EmailAttachment = Union[tuple[str, bytes, str], tuple[str, str, str]]


def send_email(
    subject: str,
    to_emails: str | list[str],
    template_name: str,
    context: dict[str, Any],
    from_email: str | None = None,
    cc_emails: str | list[str] | None = None,
    bcc_emails: str | list[str] | None = None,
    attachments: list[EmailAttachment] | None = None,
    tags: list[str] | None = None,
    headers: dict[str, str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """
    Send an email using Django's email functionality with Anymail/Postmark integration.

    Args:
        subject: Email subject
        to_emails: Recipient email or list of emails
        template_name: Template name (without extension) in EMAIL_TEMPLATE_DIR
        context: Template context variables
        from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
        cc_emails: Carbon copy recipients
        bcc_emails: Blind carbon copy recipients
        attachments: List of attachments as (filename, content, mimetype) tuples
        tags: List of tags for email tracking
        headers: Additional email headers
        metadata: Additional metadata for tracking

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not from_email:
        from_email = settings.DEFAULT_FROM_EMAIL

    # Convert single email strings to lists
    if isinstance(to_emails, str):
        to_emails = [to_emails]
    if isinstance(cc_emails, str) and cc_emails:
        cc_emails = [cc_emails]
    if isinstance(bcc_emails, str) and bcc_emails:
        bcc_emails = [bcc_emails]

    # Ensure email template exists
    template_dir = getattr(settings, "EMAIL_TEMPLATE_DIR", "emails")
    text_template = f"{template_dir}/{template_name}.txt"
    html_template = f"{template_dir}/{template_name}.html"

    try:
        # Render the email templates
        text_content = render_to_string(text_template, context)
        html_content = None

        try:
            html_content = render_to_string(html_template, context)
        except Exception as e:
            logger.warning(f"HTML template not found for {template_name}: {e}")

        # Create appropriate email message
        if html_content:
            # Create message with both text and HTML versions
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=to_emails,
                cc=cc_emails,
                bcc=bcc_emails,
                headers=headers or {},
            )
            email.attach_alternative(html_content, "text/html")
        else:
            # Plain text only
            email_message = EmailMessage(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=to_emails,
                cc=cc_emails,
                bcc=bcc_emails,
                headers=headers or {},
            )
            # Convert EmailMessage to EmailMultiAlternatives for type consistency
            email = cast(EmailMultiAlternatives, email_message)

        # Add any attachments
        if attachments:
            for attachment in attachments:
                email.attach(*attachment)

        # Add Anymail-specific attributes if using Anymail backend
        if hasattr(email, "anymail_msg"):
            if tags:
                email.anymail_msg.tags = tags
            if metadata:
                email.anymail_msg.metadata = metadata

        # Send the email
        email.send(fail_silently=False)
        logger.info(f"Email sent to {', '.join(to_emails)} with subject: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_emails}: {e}")
        return False


def send_welcome_email(user_email: str, username: str) -> bool:
    """
    Send a welcome email to a new user.

    Args:
        user_email: The user's email address
        username: The user's name or username

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    subject = "Welcome to GithubMe!"
    context = {"username": username, "email_address": user_email}
    return send_email(
        subject=subject,
        to_emails=user_email,
        template_name="welcome",
        context=context,
        tags=["welcome", "onboarding"],
    )


def send_password_reset_email(user_email: str, reset_url: str) -> bool:
    """
    Send a password reset email.

    Args:
        user_email: The user's email address
        reset_url: The password reset URL

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    subject = "Reset Your GithubMe Password"
    context = {"reset_url": reset_url}
    return send_email(
        subject=subject,
        to_emails=user_email,
        template_name="password_reset",
        context=context,
        tags=["password-reset"],
    )
