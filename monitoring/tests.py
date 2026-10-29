from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import HealthCheck, Incident, Service, Subscription


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
