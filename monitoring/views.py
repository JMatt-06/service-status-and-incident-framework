from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AccountCreationForm, HealthCheckForm, IncidentForm, ServiceForm
from .models import Incident, Service, Subscription
from .permissions import can_manage_service, is_service_owner


def health(request):
    return JsonResponse({"status": "ok"})


def status_page(request):
    active_incidents = Incident.objects.exclude(
        status=Incident.Status.CLOSED
    ).prefetch_related("affected_services")
    return render(
        request,
        "monitoring/status.html",
        {
            "services": Service.objects.all(),
            "active_incidents": active_incidents,
            "can_register_service": is_service_owner(request.user),
        },
    )


def account_create(request):
    if request.user.is_authenticated:
        return redirect("status")
    if request.method == "POST":
        form = AccountCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.groups.add(Group.objects.get(name="Service Owners"))
            login(request, user)
            return redirect("status")
    else:
        form = AccountCreationForm()
    return render(request, "registration/account_create.html", {"form": form})


@login_required
@user_passes_test(is_service_owner)
def service_create(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.owner = request.user
            service.save()
            return redirect("status")
    else:
        form = ServiceForm()
    return render(
        request, "monitoring/form.html", {"form": form, "title": "Register service"}
    )


@login_required
@user_passes_test(is_service_owner)
def health_check_configure(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    if not can_manage_service(request.user, service):
        return HttpResponseForbidden("You do not own this service.")
    health_check = getattr(service, "health_check", None)
    if request.method == "POST":
        form = HealthCheckForm(request.POST, instance=health_check)
        if form.is_valid():
            configured_check = form.save(commit=False)
            configured_check.service = service
            configured_check.save()
            return redirect("status")
    else:
        form = HealthCheckForm(instance=health_check)
    return render(
        request,
        "monitoring/form.html",
        {"form": form, "title": f"Configure {service.name}"},
    )


@login_required
@user_passes_test(is_service_owner)
def incident_create(request):
    if request.method == "POST":
        form = IncidentForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.created_by = request.user
            incident.save()
            form.save_m2m()
            return redirect("status")
    else:
        form = IncidentForm()
    return render(
        request, "monitoring/form.html", {"form": form, "title": "Create incident"}
    )


@login_required
@user_passes_test(is_service_owner)
def incident_update(request, incident_id):
    incident = get_object_or_404(Incident, pk=incident_id)
    if (
        not request.user.is_superuser
        and not incident.affected_services.filter(owner=request.user).exists()
    ):
        return HttpResponseForbidden("You do not own an affected service.")
    if request.method == "POST":
        form = IncidentForm(request.POST, instance=incident)
        if form.is_valid():
            form.save()
            return redirect("status")
    else:
        form = IncidentForm(instance=incident)
    return render(
        request,
        "monitoring/form.html",
        {"form": form, "title": f"Update {incident.title}"},
    )


@login_required
def subscribe(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    Subscription.objects.get_or_create(user=request.user, service=service)
    return redirect("status")


@login_required
def unsubscribe(request, service_id):
    Subscription.objects.filter(user=request.user, service_id=service_id).delete()
    return redirect("status")
