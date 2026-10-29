from django.contrib import admin

from .models import HealthCheck, HealthCheckResult, Incident, Service, Subscription


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "status", "created_at"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(HealthCheck)
class HealthCheckAdmin(admin.ModelAdmin):
    list_display = ["service", "url", "interval_seconds", "enabled"]


@admin.register(HealthCheckResult)
class HealthCheckResultAdmin(admin.ModelAdmin):
    list_display = ["health_check", "succeeded", "checked_at"]
    list_filter = ["succeeded"]


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "created_by", "updated_at"]
    list_filter = ["status"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "service", "created_at"]
