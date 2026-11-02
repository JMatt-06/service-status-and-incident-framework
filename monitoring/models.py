import time
import urllib.error
import urllib.request
from typing import ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Service(models.Model):
    class Status(models.TextChoices):
        OPERATIONAL = "operational", "Operational"
        DEGRADED = "degraded", "Degraded"
        UNAVAILABLE = "unavailable", "Unavailable"

    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_services",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPERATIONAL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["name"]

    def __str__(self):
        return self.name

    def update_status_from_health_check(self, result):
        if result.succeeded:
            self.status = self.Status.OPERATIONAL
        else:
            consecutive_failures = 0
            for previous_result in self.health_check.results.all():
                if previous_result.pk == result.pk:
                    continue
                if previous_result.succeeded:
                    break
                consecutive_failures += 1
            consecutive_failures += 1
            self.status = (
                self.Status.UNAVAILABLE
                if consecutive_failures >= self.health_check.failure_threshold
                else self.Status.DEGRADED
            )
        self.save(update_fields=["status", "updated_at"])


class HealthCheck(models.Model):
    service = models.OneToOneField(
        Service, on_delete=models.CASCADE, related_name="health_check"
    )
    url = models.URLField()
    interval_seconds = models.PositiveIntegerField(default=300)
    timeout_seconds = models.PositiveIntegerField(default=10)
    failure_threshold = models.PositiveIntegerField(default=3)
    enabled = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Health check for {self.service}"

    def run(self):
        started_at = time.monotonic()
        succeeded = False
        response_time_ms = None
        error_message = ""
        try:
            with urllib.request.urlopen(
                self.url, timeout=self.timeout_seconds
            ) as response:
                response_time_ms = round((time.monotonic() - started_at) * 1000)
                succeeded = 200 <= response.status < 400
                if not succeeded:
                    error_message = f"HTTP {response.status}"
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            response_time_ms = round((time.monotonic() - started_at) * 1000)
            error_message = str(error)

        result = HealthCheckResult.objects.create(
            health_check=self,
            succeeded=succeeded,
            response_time_ms=response_time_ms,
            error_message=error_message,
        )
        self.last_run_at = result.checked_at
        self.save(update_fields=["last_run_at"])
        self.service.update_status_from_health_check(result)
        return result


class HealthCheckResult(models.Model):
    health_check = models.ForeignKey(
        HealthCheck, on_delete=models.CASCADE, related_name="results"
    )
    succeeded = models.BooleanField()
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-checked_at"]


class Incident(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        INVESTIGATING = "investigating", "Investigating"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN
    )
    post_mortem_summary = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_incidents",
    )
    affected_services = models.ManyToManyField(Service, related_name="incidents")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.status == self.Status.CLOSED and not self.post_mortem_summary.strip():
            raise ValidationError(
                {
                    "post_mortem_summary": "A post-mortem summary is required to close an incident."
                }
            )

    def __str__(self):
        return self.title


class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions"
    )
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="subscriptions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints: ClassVar[list[models.UniqueConstraint]] = [
            models.UniqueConstraint(
                fields=["user", "service"], name="unique_user_service_subscription"
            )
        ]
