# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_user_stripe_customer_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="tour_completed",
            field=models.BooleanField(
                default=False,
                help_text="Whether the user has completed the onboarding tour"
            ),
        ),
    ]
