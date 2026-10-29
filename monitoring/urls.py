from django.urls import path

from . import views

urlpatterns = [
    path("", views.status_page, name="status"),
    path("health/", views.health, name="health"),
    path("services/new/", views.service_create, name="service-create"),
    path(
        "services/<int:service_id>/health-check/",
        views.health_check_configure,
        name="health-check-configure",
    ),
    path("incidents/new/", views.incident_create, name="incident-create"),
    path(
        "incidents/<int:incident_id>/edit/",
        views.incident_update,
        name="incident-update",
    ),
    path("services/<int:service_id>/subscribe/", views.subscribe, name="subscribe"),
    path(
        "services/<int:service_id>/unsubscribe/", views.unsubscribe, name="unsubscribe"
    ),
]
