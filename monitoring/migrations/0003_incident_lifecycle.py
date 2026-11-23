from typing import ClassVar

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies: ClassVar = [
        ("monitoring", "0002_create_service_owner_group"),
    ]

    operations: ClassVar = [
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
