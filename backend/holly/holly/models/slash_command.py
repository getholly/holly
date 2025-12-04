from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db import models

User = get_user_model()


class SlashCommand(models.Model):
    """
    User-defined or system slash command.

    Commands can be either:
    - String replacements (command_type='replacement')
    - Python function calls (command_type='function')

    Access control: Users can only access their own commands + system commands.
    """

    COMMAND_TYPE_CHOICES = [
        ('replacement', 'String Replacement'),
        ('function', 'Python Function'),
    ]

    # Primary Key
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    # Ownership
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="slash_commands",
        null=True,
        blank=True,
        help_text="Owner of the command. NULL for system commands."
    )
    is_system = models.BooleanField(
        default=False,
        db_index=True,
        help_text="System commands are available to all users"
    )

    # Command Definition
    name = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_-]+$',
                message='Command name can only contain letters, numbers, hyphens, and underscores'
            )
        ],
        help_text="Command name without the leading slash (e.g., 'summarize')"
    )
    command_type = models.CharField(
        max_length=20,
        choices=COMMAND_TYPE_CHOICES,
        default='replacement'
    )
    description = models.TextField(
        blank=True,
        help_text="User-friendly description of what the command does"
    )

    # Replacement Command Fields
    replacement_text = models.TextField(
        blank=True,
        help_text="Template text with {arg1}, {arg2} placeholders for replacement commands"
    )

    # Function Command Fields
    function_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Python import path (e.g., 'holly.holly.services.command_handlers.summarize_conversation')"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Inactive commands won't be executed"
    )
    usage_count = models.IntegerField(
        default=0,
        help_text="Track how often this command is used"
    )

    class Meta:
        db_table = 'slash_commands'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'name'], name='idx_user_name'),
            models.Index(fields=['is_system', 'name'], name='idx_system_name'),
            models.Index(fields=['is_active', 'name'], name='idx_active_name'),
        ]
        constraints = [
            # Ensure system commands have no user
            models.CheckConstraint(
                check=(
                    models.Q(is_system=False, user__isnull=False) |
                    models.Q(is_system=True, user__isnull=True)
                ),
                name='system_command_no_user'
            ),
            # Ensure replacement commands have replacement_text
            models.CheckConstraint(
                check=(
                    models.Q(command_type='replacement', replacement_text__gt='') |
                    ~models.Q(command_type='replacement')
                ),
                name='replacement_has_text'
            ),
            # Ensure function commands have function_path
            models.CheckConstraint(
                check=(
                    models.Q(command_type='function', function_path__gt='') |
                    ~models.Q(command_type='function')
                ),
                name='function_has_path'
            ),
            # Unique constraint: user+name or system+name
            models.UniqueConstraint(
                fields=['user', 'name'],
                condition=models.Q(user__isnull=False),
                name='unique_user_command_name'
            ),
            models.UniqueConstraint(
                fields=['name'],
                condition=models.Q(is_system=True),
                name='unique_system_command_name'
            ),
        ]

    def __str__(self):
        prefix = "System" if self.is_system else f"User({self.user_id})"
        return f"{prefix}: /{self.name}"

    def clean(self):
        """Model-level validation"""
        from django.core.exceptions import ValidationError

        errors = {}

        # Validate system command has no user
        if self.is_system and self.user_id is not None:
            errors['user'] = "System commands cannot have a user"

        # Validate non-system command has user
        if not self.is_system and self.user_id is None:
            errors['user'] = "Non-system commands must have a user"

        # Validate replacement command has replacement_text
        if self.command_type == 'replacement' and not self.replacement_text:
            errors['replacement_text'] = "Replacement commands must have replacement text"

        # Validate function command has function_path
        if self.command_type == 'function' and not self.function_path:
            errors['function_path'] = "Function commands must have a function path"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
