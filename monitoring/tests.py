from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import HealthCheck, HealthCheckResult, Incident, Service, Subscription


class MonitoringModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password")
        self.regular_user = User.objects.create_user(
            username="user", password="password"
        )
        self.owner.groups.add(Group.objects.get(name="Service Owners"))
        self.service = Service.objects.create(name="API", slug="api", owner=self.owner)

    def test_service_owner_can_register_service(self):
        self.client.login(username="owner", password="password")
        response = self.client.post(
            reverse("service-create"),
            {"name": "Web", "slug": "web", "description": "Frontend"},
        )
        self.assertRedirects(response, reverse("status"))
        self.assertTrue(Service.objects.filter(slug="web", owner=self.owner).exists())

    def test_regular_user_cannot_register_service(self):
        self.client.login(username="user", password="password")
        response = self.client.post(
            reverse("service-create"), {"name": "Web", "slug": "web"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Service.objects.filter(slug="web").exists())

    def test_signing_out_returns_to_sign_in_page(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertContains(self.client.get(reverse("login")), "Create an account")

    def test_visitor_can_create_account_and_register_service(self):
        response = self.client.post(
            reverse("account-create"),
            {
                "username": "new-owner",
                "password1": "a-strong-password-123",
                "password2": "a-strong-password-123",
            },
        )
        self.assertRedirects(response, reverse("status"))
        new_owner = User.objects.get(username="new-owner")
        self.assertTrue(new_owner.groups.filter(name="Service Owners").exists())
        self.assertEqual(int(self.client.session["_auth_user_id"]), new_owner.id)

        response = self.client.post(
            reverse("service-create"),
            {"name": "Web", "slug": "web", "description": "Frontend"},
        )
        self.assertRedirects(response, reverse("status"))
        self.assertTrue(Service.objects.filter(slug="web", owner=new_owner).exists())

    def test_account_creation_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("account-create"),
            {
                "username": "new-user",
                "password1": "a-strong-password-123",
                "password2": "a-different-password-456",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="new-user").exists())

    def test_service_owner_can_configure_health_check(self):
        self.client.login(username="owner", password="password")
        response = self.client.post(
            reverse("health-check-configure", args=[self.service.id]),
            {
                "url": "https://api.example.com/health",
                "interval_seconds": 60,
                "timeout_seconds": 5,
                "failure_threshold": 2,
                "enabled": "on",
            },
        )
        self.assertRedirects(response, reverse("status"))
        health_check = HealthCheck.objects.get(service=self.service)
        self.assertEqual(health_check.url, "https://api.example.com/health")
        self.assertEqual(health_check.interval_seconds, 60)
        self.assertEqual(health_check.timeout_seconds, 5)
        self.assertEqual(health_check.failure_threshold, 2)
        self.assertTrue(health_check.enabled)

    def test_service_owner_cannot_configure_another_owners_health_check(self):
        other_owner = User.objects.create_user(
            username="other-owner", password="password"
        )
        other_owner.groups.add(Group.objects.get(name="Service Owners"))
        other_service = Service.objects.create(
            name="Other API", slug="other-api", owner=other_owner
        )

        self.client.login(username="owner", password="password")
        response = self.client.post(
            reverse("health-check-configure", args=[other_service.id]),
            {
                "url": "https://api.example.com/health",
                "interval_seconds": 60,
                "timeout_seconds": 5,
                "failure_threshold": 2,
                "enabled": "on",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(HealthCheck.objects.filter(service=other_service).exists())

    @patch("monitoring.models.urllib.request.urlopen")
    def test_owner_can_run_health_check_and_update_status(self, urlopen):
        response = urlopen.return_value.__enter__.return_value
        response.status = 200
        health_check = HealthCheck.objects.create(
            service=self.service,
            url="https://api.example.com/health",
            failure_threshold=2,
        )

        self.client.login(username="owner", password="password")
        request_time = health_check.last_run_at
        result = self.client.post(reverse("health-check-run", args=[self.service.id]))

        self.assertRedirects(result, reverse("status"))
        stored_result = HealthCheckResult.objects.get(health_check=health_check)
        self.assertTrue(stored_result.succeeded)
        self.assertIsNotNone(stored_result.checked_at)
        self.assertNotEqual(stored_result.checked_at, request_time)
        self.assertEqual(
            HealthCheck.objects.get(pk=health_check.pk).last_run_at,
            stored_result.checked_at,
        )
        self.assertEqual(Service.objects.get(pk=self.service.pk).status, "operational")

    @patch("monitoring.models.urllib.request.urlopen")
    def test_status_page_and_health_history_display_check_results(self, urlopen):
        response = urlopen.return_value.__enter__.return_value
        response.status = 200
        health_check = HealthCheck.objects.create(
            service=self.service,
            url="https://api.example.com/health",
        )
        self.client.force_login(self.owner)

        self.client.post(reverse("health-check-run", args=[self.service.id]))

        status_response = self.client.get(reverse("status"))
        self.assertContains(status_response, "Latest check:")
        self.assertContains(
            status_response, reverse("health-history", args=[self.service.slug])
        )

        history_response = self.client.get(
            reverse("health-history", args=[self.service.slug])
        )
        self.assertEqual(history_response.status_code, 200)
        self.assertContains(history_response, "Passed")
        self.assertContains(
            history_response, "No health checks have been recorded.", count=0
        )
        self.assertEqual(health_check.results.count(), 1)

    def test_health_history_is_public_and_handles_unconfigured_service(self):
        response = self.client.get(reverse("health-history", args=[self.service.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No health checks have been recorded.")

    @patch("monitoring.models.urllib.request.urlopen")
    def test_failed_health_checks_degrade_then_unavailable_service(self, urlopen):
        urlopen.side_effect = TimeoutError("health check timed out")
        health_check = HealthCheck.objects.create(
            service=self.service,
            url="https://api.example.com/health",
            failure_threshold=2,
        )
        self.client.login(username="owner", password="password")

        self.client.post(reverse("health-check-run", args=[self.service.id]))
        self.assertEqual(
            Service.objects.get(pk=self.service.pk).status, Service.Status.DEGRADED
        )
        self.client.post(reverse("health-check-run", args=[self.service.id]))
        self.assertEqual(
            Service.objects.get(pk=self.service.pk).status, Service.Status.UNAVAILABLE
        )
        self.assertEqual(health_check.results.count(), 2)
        self.assertTrue(health_check.results.first().error_message)

    def test_service_owner_cannot_run_another_owners_health_check(self):
        other_owner = User.objects.create_user(
            username="other-owner", password="password"
        )
        other_service = Service.objects.create(
            name="Other API", slug="other-api", owner=other_owner
        )
        HealthCheck.objects.create(
            service=other_service, url="https://api.example.com/health"
        )

        self.client.login(username="owner", password="password")
        response = self.client.post(
            reverse("health-check-run", args=[other_service.id])
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(HealthCheckResult.objects.count(), 0)

    def test_owner_can_subscribe_and_unsubscribe(self):
        self.client.login(username="owner", password="password")
        self.client.post(reverse("subscribe", args=[self.service.id]))
        self.assertTrue(
            Subscription.objects.filter(user=self.owner, service=self.service).exists()
        )
        self.client.post(reverse("unsubscribe", args=[self.service.id]))
        self.assertFalse(
            Subscription.objects.filter(user=self.owner, service=self.service).exists()
        )

    def test_closed_incident_requires_post_mortem(self):
        incident = Incident(
            title="Outage",
            description="The API is unavailable",
            status=Incident.Status.CLOSED,
            created_by=self.owner,
        )
        with self.assertRaises(ValidationError):
            incident.full_clean()
