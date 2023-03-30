import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from catalog.errors import FetchError
from gh import fetch
from services import forms, models
from systemlogs.models import add_error, add_info


class UserError(Exception):
    pass


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            type=str,
            help="The username of a user with a GitHub login.",
        )
        parser.add_argument(
            "--source",
            type=str,
            help="The slug of a source to refresh.",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Refresh all sources to refresh.",
        )

    def handle(self, *args, **options):
        username = options.get("user") or os.environ.get("CRON_USER")
        if not username:
            raise UserError(
                "User must be set either using `--cron-user` or `CRON_USER` as the username of a user with a GitHub login."
            )

        user = User.objects.get(username=username)

        class requestStub:
            def __init__(self, user):
                self.user = user

        if not options.get("source") and not options.get("all"):
            raise ValueError("Either `--source` or `--all` must be set.")

        if options.get("all"):
            queryset = models.Source.objects.all()

        if options.get("source"):
            queryset = models.Source.objects.filter(slug=options.get("source"))

        request = requestStub(user)
        outputs = []

        for source in queryset:
            try:
                results = fetch.get(user, source)
            except FetchError as error:
                add_error(source, error.message, request=request)
                continue

            for data in results:
                form = forms.ServiceForm({"data": data["contents"]})
                form.source = source
                if not form.is_valid():
                    message = f"Background validation failed for: `{source.url}`. Error: {form.nice_errors()}."
                    add_error(source, message, request=request)
                    continue

                output = form.save()
                for log in output["logs"]:
                    add_info(source, log, request=request)
                outputs.append(output)

        return {"queryset": queryset, "outputs": outputs}
