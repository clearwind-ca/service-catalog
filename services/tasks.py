from catalog.celery import app
from catalog.errors import FetchError
from gh import fetch
from services import forms
from services.models import Organization, Source
from web.shortcuts import get_object_or_None

import logging
logger = logging.getLogger(__name__)

@app.task
def refresh_source_from_github(source_slug):
    logger.info(f"Task: refreshing from source: {source_slug}")
    source = Source.objects.get(slug=source_slug)
    try:
        results = fetch.get(source)
    except FetchError as error:
        return False

    for data in results:
        form = forms.ServiceForm({"data": data["contents"]})
        form.source = source
        if not form.is_valid():
            logging.error(form.errors)
            return False

        form.save()


@app.task
def refresh_sources_from_github():
    logger.info(f"Task: refreshing sources from github")
    for source in Source.objects.filter(active=True):
        refresh_source_from_github.delay(source.slug)


@app.task
def refresh_org_from_github(org_slug):
    logger.info(f"Task: refreshing org from github {org_slug}")
    try:
        results = fetch.get_repositories(org_slug)
    except FetchError as error:
        return False

    # Results is giving the same repository multiple times, not sure why yet. 
    # So we'll dedupe.
    dedupe = set()
    for repo in results:
        logger.info(f"repo {repo}")
        # If no source exists at this url, create one.
        slug = None
        existing = get_object_or_None(Source, url=repo.html_url)
        if not existing:
            form = forms.SourceForm({"url": repo.html_url, "active": True})
            if not form.is_valid():
                logging.error(form.errors)
                continue

            form.save()
            slug = form.instance.slug
        else:
            slug = existing.slug
        dedupe.add(slug)

    for slug in dedupe:
        refresh_source_from_github.delay(slug)


@app.task
def refresh_sources_from_orgs(): 
    logger.info(f"Task: refreshing sources from orgs")
    for org in Organization.objects.filter(active=True, auto_add_sources=True):
        refresh_org_from_github.delay(org.name)


@app.task
def refresh_orgs_from_github():
    logger.info(f"Task: refreshing orgs from github")
    for org in fetch.get_orgs():
        org_obj = get_object_or_None(Organization, name=org["login"])
        if not org_obj:
            Organization.objects.create(
                name=org["login"],
                active=True,
                auto_add_sources=True,
                url=org["html_url"],
                raw_data=org["raw_data"],
            )

    refresh_sources_from_orgs.delay()
