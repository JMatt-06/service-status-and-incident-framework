from typing import ClassVar

from django.contrib import admin

from .models import HealthCheck, HealthCheckResult, Incident, Service, Subscription


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display: ClassVar[list[str]] = ["name", "owner", "status", "created_at"]
    prepopulated_fields: ClassVar[dict[str, tuple[str, ...]]] = {"slug": ("name",)}


@admin.register(HealthCheck)
class HealthCheckAdmin(admin.ModelAdmin):
    list_display: ClassVar[list[str]] = [
        "service",
        "url",
        "interval_seconds",
        "enabled",
    ]


@admin.register(HealthCheckResult)
class HealthCheckResultAdmin(admin.ModelAdmin):
    list_display: ClassVar[list[str]] = ["health_check", "succeeded", "checked_at"]
    list_filter: ClassVar[list[str]] = ["succeeded"]


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display: ClassVar[list[str]] = ["title", "status", "created_by", "updated_at"]
    list_filter: ClassVar[list[str]] = ["status"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display: ClassVar[list[str]] = ["user", "service", "created_at"]
