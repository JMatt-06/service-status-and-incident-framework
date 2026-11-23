from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("monitoring", "0003_incident_lifecycle"),
    ]

    operations = [
        migrations.AddField(
            model_name="incident",
            name="detection_source",
            field=models.CharField(
                choices=[
                    ("manual", "Manual"),
                    ("health_check", "Health check"),
                ],
                default="manual",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="incident",
            name="health_check",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="incidents",
                to="monitoring.healthcheck",
            ),
        ),
    ]
