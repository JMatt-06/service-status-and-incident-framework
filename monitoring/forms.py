from typing import ClassVar

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import HealthCheck, Incident, Service


class AccountCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields: ClassVar[list[str]] = ["username", "password1", "password2"]


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields: ClassVar[list[str]] = ["name", "slug", "description"]


class HealthCheckForm(forms.ModelForm):
    class Meta:
        model = HealthCheck
        fields: ClassVar[list[str]] = [
            "url",
            "interval_seconds",
            "timeout_seconds",
            "failure_threshold",
            "enabled",
        ]


class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields: ClassVar[list[str]] = [
            "title",
            "description",
            "status",
            "post_mortem_summary",
            "affected_services",
        ]
        widgets: ClassVar[dict[str, object]] = {
            "affected_services": forms.CheckboxSelectMultiple
        }

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get("status") == Incident.Status.CLOSED
            and not cleaned_data.get("post_mortem_summary", "").strip()
        ):
            self.add_error(
                "post_mortem_summary",
                "A post-mortem summary is required to close an incident.",
            )
        return cleaned_data
