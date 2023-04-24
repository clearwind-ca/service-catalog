import os
import time

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from catalog.errors import NoRepository, SendError
from gh import send
from health.models import Check, CheckResult
from services.models import Service


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            type=str,
            help="The slug of the check to send.",
        )
        parser.add_argument(
            "--all-checks",
            action="store_true",
            help="Send all the checks.",
        )
        parser.add_argument(
            "--service",
            type=str,
            help="The slug of the service to check.",
        )
        parser.add_argument(
            "--all-services",
            action="store_true",
            help="Send all the services.",
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Print out less.",
        )
        parser.add_argument(
            "--user",
            type=str,
            help="The username of a user with a GitHub login.",
        )

    def handle(self, *args, **options):
        username = options.get("user") or os.environ.get("CRON_USER")
        quiet = options.get("quiet", False)
        if not username:
            raise ValueError(
                "User must be set either using `--cron-user` or `CRON_USER` as the username of a user with a GitHub login."
            )
        user = User.objects.get(username=username)

        class requestStub:
            def __init__(self, user):
                self.user = user

        if not options.get("check") and not options.get("all_checks"):
            raise ValueError("Either `--check` or `--all-checks` must be set.")

        if not options.get("service") and not options.get("all_services"):
            raise ValueError("Either `--service` or `--all-services` must be set.")

        if options.get("all_checks"):
            check_queryset = Check.objects.all()

        if options.get("check"):
            check_queryset = Check.objects.filter(slug=options.get("check"))

        if options.get("all_services"):
            service_queryset = Service.objects.all()

        if options.get("service"):
            service_queryset = Service.objects.filter(slug=options.get("service"))

        request = requestStub(user)
        k = 0
        for check in check_queryset:
            for service in service_queryset:
                result = CheckResult.objects.create(
                    health_check=check,
                    status="sent",
                    service=service,
                )
                try:
                    send.dispatch(user, result)
                except (SendError, NoRepository) as error:
                    # Fatal error, they are all going to fail.
                    # Should we log here?
                    result.status = "error"
                    result.save()
                    raise error

                k += 1
                time.sleep(settings.SEND_CHECKS_DELAY)

        if not quiet:
            print(f"Sent {k} checks to GitHub.")
