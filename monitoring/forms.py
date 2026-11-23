from typing import ClassVar

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import models

from .models import HealthCheck, Incident, Service


class AccountCreationForm(UserCreationForm):
    class AccountType(models.TextChoices):
        ADMIN = "admin", "Admin - manage services and incidents"
        SUBSCRIBER = "subscriber", "Subscriber - subscribe to services"

    account_type = forms.ChoiceField(
        choices=AccountType.choices,
        initial=AccountType.SUBSCRIBER,
        required=False,
        widget=forms.RadioSelect,
        label="Account type",
    )

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
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            status = self.instance.status
            allowed_statuses = (status,) + Incident.STATUS_TRANSITIONS.get(status, ())
            self.fields["status"].choices = [
                choice
                for choice in Incident.Status.choices
                if choice[0] in allowed_statuses
            ]
        if user is not None:
            services = Service.objects.all()
            if not user.is_superuser:
                services = services.filter(owner=user)
            self.fields["affected_services"].queryset = services
        self.fields["affected_services"].required = True
        self.fields[
            "affected_services"
        ].help_text = "Select at least one affected service."

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("affected_services"):
            self.add_error(
                "affected_services",
                "Select at least one affected service.",
            )
        if (
            cleaned_data.get("status") == Incident.Status.CLOSED
            and not cleaned_data.get("post_mortem_summary", "").strip()
        ):
            self.add_error(
                "post_mortem_summary",
                "A post-mortem summary is required to close an incident.",
            )
        return cleaned_data

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
