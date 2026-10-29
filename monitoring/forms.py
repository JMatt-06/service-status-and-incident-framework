from django import forms

from .models import HealthCheck, Incident, Service


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "slug", "description"]


class HealthCheckForm(forms.ModelForm):
    class Meta:
        model = HealthCheck
        fields = ["url", "interval_seconds", "timeout_seconds", "failure_threshold", "enabled"]


class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = ["title", "description", "status", "post_mortem_summary", "affected_services"]
        widgets = {"affected_services": forms.CheckboxSelectMultiple}

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("status") == Incident.Status.CLOSED and not cleaned_data.get("post_mortem_summary", "").strip():
            self.add_error("post_mortem_summary", "A post-mortem summary is required to close an incident.")
        return cleaned_data
