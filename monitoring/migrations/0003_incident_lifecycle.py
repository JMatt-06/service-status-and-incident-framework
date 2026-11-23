from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("monitoring", "0002_create_service_owner_group"),
    ]

    operations = [
        migrations.AddField(
            model_name="incident",
            name="closed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="resolved_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
