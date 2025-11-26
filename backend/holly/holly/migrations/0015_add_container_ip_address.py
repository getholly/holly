from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("holly", "0014_missionrepos_alter_mission_repositories"),
    ]

    operations = [
        migrations.AddField(
            model_name="mission",
            name="container_ip_address",
            field=models.CharField(
                max_length=64,
                blank=True,
                null=True,
                help_text="IP address of the running container",
                verbose_name="Container IP Address",
            ),
        ),
    ]
