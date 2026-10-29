# service-status-and-incident-framework
Develop a web-based Service Status and Incident Framework that allows organizers to monitor the uptime and downtime of their services and be able to communicate service problems to users. The system will provide a status page showing whether or not services are operational or not.
The goal is to provide a simple framework that helps
I hope this works
Lets hope this works 2

## Getting started

This project uses Django with SQLite for local persistence.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/` for the public status page and `/admin/` for administration.
Create a user in the Django admin, add that user to the automatically-created `Service Owners`
group, and assign ownership when registering services. Service owners can register services,
configure health-check settings, and manage incidents; authenticated regular users can subscribe.

Run the automated tests with:

```bash
python manage.py test
```

## Structure

- `status_framework/` contains Django settings and project routing.
- `monitoring/` contains service, health-check, incident, and subscription models, authorization helpers, views, and tests.
- `templates/` contains the initial status page and authenticated forms.
- `docs/adr/` records the service-owner authorization decision.
