from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Incident, Service, Subscription


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
