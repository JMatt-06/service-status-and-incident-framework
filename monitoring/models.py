from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Service(models.Model):
    class Status(models.TextChoices):
        OPERATIONAL = "operational", "Operational"
        DEGRADED = "degraded", "Degraded"
        UNAVAILABLE = "unavailable", "Unavailable"

    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_services")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPERATIONAL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class HealthCheck(models.Model):
    service = models.OneToOneField(Service, on_delete=models.CASCADE, related_name="health_check")
    url = models.URLField()
    interval_seconds = models.PositiveIntegerField(default=300)
    timeout_seconds = models.PositiveIntegerField(default=10)
    failure_threshold = models.PositiveIntegerField(default=3)
    enabled = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Health check for {self.service}"


class HealthCheckResult(models.Model):
    health_check = models.ForeignKey(HealthCheck, on_delete=models.CASCADE, related_name="results")
    succeeded = models.BooleanField()
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-checked_at"]


class Incident(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        INVESTIGATING = "investigating", "Investigating"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    post_mortem_summary = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_incidents")
    affected_services = models.ManyToManyField(Service, related_name="incidents")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.status == self.Status.CLOSED and not self.post_mortem_summary.strip():
            raise ValidationError({"post_mortem_summary": "A post-mortem summary is required to close an incident."})

    def __str__(self):
        return self.title


class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="subscriptions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "service"], name="unique_user_service_subscription")]
