from catalog.celery import app
from catalog.errors import FetchError
from gh import fetch
from services import forms
from services.models import Organization, Source


@app.task
def refresh_from_github(username, source_slug):
    source = Source.objects.get(slug=source_slug)
    try:
        results = fetch.get(username, source)
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
def refresh_active_from_github(username):
    for source in Source.objects.filter(active=True):
        refresh_from_github.delay(username, source.slug)


@app.task
def refresh_sources_from_github(username, org_slug):
    try:
        results = fetch.get_repositories(username, org_slug)
    except FetchError as error:
        return False

    for repo in results:
        form = forms.SourceForm({"url": repo.html_url, "active": True})
        if not form.is_valid():
            print(form.errors)
            continue

        form.save()


@app.task
def refresh_org_from_github(username):
    for org in Organization.objects.filter(active=True, auto_add_sources=True):
        refresh_sources_from_github.delay(username, org.name)
