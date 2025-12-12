from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Tools(models.Model):
    """
    Model representing MCP Tools configuration.

    Supports both stdio (local subprocess) and remote (HTTP/SSE) MCP servers.
    Remote servers can require authentication, which is stored per-user in ToolAuth.
    """

    name = models.CharField(
        _("Name"),
        max_length=64,
        unique=True,
        help_text=_("The name of the MCP tool"),
    )
    description = models.TextField(help_text="Description of this MCP tool")
    config = models.JSONField(help_text=_("MCP server configuration (command/url/args/etc)"))

    # Remote MCP server fields
    is_remote = models.BooleanField(
        _("Is Remote"),
        default=False,
        help_text=_("Whether this is a remote MCP server (HTTP/SSE) or stdio"),
    )
    requires_auth = models.BooleanField(
        _("Requires Authentication"),
        default=False,
        help_text=_("Whether this tool requires authentication (OAuth, API key, etc.)"),
    )

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Tool")
        verbose_name_plural = _("Tools")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ToolAuth(models.Model):
    """
    Model for storing per-user authentication tokens for remote MCP tools.

    Each user can have their own authentication credentials for remote tools.
    Supports OAuth, API keys, and bearer tokens.
    """

    class AuthType(models.TextChoices):
        OAUTH = "oauth", _("OAuth 2.0")
        API_KEY = "api_key", _("API Key")
        BEARER = "bearer", _("Bearer Token")

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tool_auths",
        help_text=_("User who owns this authentication"),
    )
    tool = models.ForeignKey(
        Tools,
        on_delete=models.CASCADE,
        related_name="user_auths",
        help_text=_("Tool this authentication is for"),
    )
    auth_type = models.CharField(
        _("Authentication Type"),
        max_length=20,
        choices=AuthType.choices,
        help_text=_("Type of authentication"),
    )
    auth_data = models.JSONField(
        help_text=_("Authentication data (tokens, keys, etc.) - stored securely")
    )

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Tool Authentication")
        verbose_name_plural = _("Tool Authentications")
        unique_together = [["user", "tool"]]
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.tool.name} ({self.auth_type})"

    def is_valid(self) -> bool:
        """
        Check if this authentication is still valid.

        For OAuth, checks if token is expired.
        For API keys/bearer tokens, always returns True.
        """
        if self.auth_type == self.AuthType.OAUTH:
            # Check if OAuth token is expired
            from datetime import datetime

            expires_at = self.auth_data.get("expires_at")
            if expires_at:
                try:
                    from dateutil.parser import parse

                    expiry = parse(expires_at)
                    return datetime.now(expiry.tzinfo) < expiry
                except (ValueError, TypeError):
                    return False
        return True

    def get_mcp_auth_config(self) -> dict:
        """
        Get authentication configuration in MCP format.

        Returns:
            Dictionary with auth configuration for MCPServerConfig
        """
        if self.auth_type == self.AuthType.OAUTH:
            return {
                "type": "oauth",
                "token": self.auth_data.get("access_token"),
                "refresh_token": self.auth_data.get("refresh_token"),
            }
        elif self.auth_type == self.AuthType.API_KEY:
            return {
                "type": "api_key",
                "token": self.auth_data.get("token"),
            }
        elif self.auth_type == self.AuthType.BEARER:
            return {
                "type": "bearer",
                "token": self.auth_data.get("token"),
            }
        return {}
