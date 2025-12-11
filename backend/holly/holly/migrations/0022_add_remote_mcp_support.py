# Generated manually for remote MCP support

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("holly", "0021_merge_20251123_2016"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add unique constraint to Tools.name
        migrations.AlterField(
            model_name="tools",
            name="name",
            field=models.CharField(
                help_text="The name of the MCP tool",
                max_length=64,
                unique=True,
                verbose_name="Name",
            ),
        ),
        # Add help_text to Tools.config
        migrations.AlterField(
            model_name="tools",
            name="config",
            field=models.JSONField(
                help_text="MCP server configuration (command/url/args/etc)"
            ),
        ),
        # Add is_remote field to Tools
        migrations.AddField(
            model_name="tools",
            name="is_remote",
            field=models.BooleanField(
                default=False,
                help_text="Whether this is a remote MCP server (HTTP/SSE) or stdio",
                verbose_name="Is Remote",
            ),
        ),
        # Add requires_auth field to Tools
        migrations.AddField(
            model_name="tools",
            name="requires_auth",
            field=models.BooleanField(
                default=False,
                help_text="Whether this tool requires authentication (OAuth, API key, etc.)",
                verbose_name="Requires Authentication",
            ),
        ),
        # Create ToolAuth model
        migrations.CreateModel(
            name="ToolAuth",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "auth_type",
                    models.CharField(
                        choices=[
                            ("oauth", "OAuth 2.0"),
                            ("api_key", "API Key"),
                            ("bearer", "Bearer Token"),
                        ],
                        help_text="Type of authentication",
                        max_length=20,
                        verbose_name="Authentication Type",
                    ),
                ),
                (
                    "auth_data",
                    models.JSONField(
                        help_text="Authentication data (tokens, keys, etc.) - stored securely"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Created At"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Updated At"),
                ),
                (
                    "tool",
                    models.ForeignKey(
                        help_text="Tool this authentication is for",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_auths",
                        to="holly.tools",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        help_text="User who owns this authentication",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tool_auths",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Tool Authentication",
                "verbose_name_plural": "Tool Authentications",
                "ordering": ["-updated_at"],
                "unique_together": {("user", "tool")},
            },
        ),
    ]
