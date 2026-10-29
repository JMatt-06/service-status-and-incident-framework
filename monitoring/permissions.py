from django.contrib.auth.models import Group


SERVICE_OWNER_GROUP = "Service Owners"


def is_service_owner(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name=SERVICE_OWNER_GROUP).exists())


def can_manage_service(user, service):
    return is_service_owner(user) and (user.is_superuser or service.owner_id == user.id)


def ensure_service_owner_group():
    group, _ = Group.objects.get_or_create(name=SERVICE_OWNER_GROUP)
    return group
