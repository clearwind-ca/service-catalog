from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from systemlogs import models


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--ago",
            type=int,
            help="Delete logs older than this in days",
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Print out less.",
        )

    def handle(self, *args, **options):
        ago = options.get("ago", None)
        quiet = options.get("quiet", False)
        if ago is None:
            raise ValueError(
                "You must specify `--ago` as the number of days to delete logs older than."
            )

        queryset = models.SystemLog.objects.filter(created__lt=timezone.now() - timedelta(days=ago))
        count = queryset.count()
        queryset.delete()
        if not quiet:
            print(f"Deleted {count} logs.")
