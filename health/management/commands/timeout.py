import os
import sys
import time
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from catalog.errors import NoRepository, SendError
from gh import send
from health.models import Check, CheckResult
from services.models import Service
from web.helpers import attempt_int


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Print out less.",
        )

    def handle(self, *args, **options):
        quiet = options.get("quiet", False)

        timeout = attempt_int(settings.CHECKS_TIMEOUT_HOURS)
        if timeout == 0 and not quiet:
            print("Timeout is set to 0, so no check results will timeout.")
            sys.exit(1)

        check_queryset = CheckResult.objects.filter(
            updated__lt=timezone.now() - timedelta(hours=timeout),
            status__in=["sent"],
        )
        for check in check_queryset:
            check.status = "timed-out"
            check.save()

        if not quiet:
            print(f"Timed out {check_queryset.count()} results.")
