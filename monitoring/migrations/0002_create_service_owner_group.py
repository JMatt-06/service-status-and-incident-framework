from typing import ClassVar

from django.db import migrations


def create_service_owner_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name="Service Owners")


def remove_service_owner_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Service Owners").delete()


class Migration(migrations.Migration):
    dependencies: ClassVar[list[tuple[str, str]]] = [("monitoring", "0001_initial")]
    operations: ClassVar[list[object]] = [
        migrations.RunPython(create_service_owner_group, remove_service_owner_group)
    ]
