from catalog.celery import app
from gh import fetch
from services import forms
from services.models import Source


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
