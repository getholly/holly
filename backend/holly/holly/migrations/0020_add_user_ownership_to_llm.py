# Generated migration for adding user ownership to LLM model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def mark_existing_llms_as_system(apps, schema_editor):
    """Mark all existing LLMs as system LLMs"""
    LLM = apps.get_model('holly', 'LLM')
    LLM.objects.all().update(is_system=True)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("holly", "0019_mission_container_started_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="llm",
            name="user",
            field=models.ForeignKey(
                blank=True,
                help_text="User who owns this LLM. Null for system LLMs.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="custom_llms",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="llm",
            name="is_system",
            field=models.BooleanField(
                default=False,
                help_text="Whether this is a system-wide LLM or user-specific",
                verbose_name="Is System LLM",
            ),
        ),
        migrations.RunPython(
            mark_existing_llms_as_system,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="llm",
            constraint=models.UniqueConstraint(
                condition=models.Q(("user__isnull", False)),
                fields=("user", "name"),
                name="unique_user_llm_name",
            ),
        ),
    ]
