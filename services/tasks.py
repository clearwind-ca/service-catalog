from catalog.celery import app
from catalog.errors import FetchError
from gh import fetch
from services import forms
from services.models import Organization, Source
from web.shortcuts import get_object_or_None

@app.task
def refresh_service_from_github(source_slug):
    source = Source.objects.get(slug=source_slug)
    try:
        results = fetch.get(source)
    except FetchError as error:
        return False

    for data in results:
        form = forms.ServiceForm({"data": data["contents"]})
        form.source = source
        if not form.is_valid():
            print(form.errors)
            return False

        form.save()


@app.task
def refresh_services_from_github():
    for source in Source.objects.filter(active=True):
        refresh_service_from_github.delay(source.slug)


@app.task
def refresh_sources_from_github(org_slug):
    try:
        results = fetch.get_repositories(org_slug)
    except FetchError as error:
        return False

    for repo in results:
        form = forms.SourceForm({"url": repo.html_url, "active": True})
        if not form.is_valid():
            print(form.errors)
            continue

        form.save()


@app.task
def refresh_sources_from_orgs():
    for org in Organization.objects.filter(active=True, auto_add_sources=True):
        refresh_sources_from_github.delay(org.name)

    refresh_services_from_github.delay()


@app.task
def refresh_orgs_from_github():
    for org in fetch.get_orgs():
        org_obj = get_object_or_None(Organization, name=org)
        if not org_obj:
            Organization.objects.create(name=org, active=True, auto_add_sources=True)
    
    refresh_sources_from_orgs.delay()