from django.core.management.base import BaseCommand

from services import models
from services.tasks import refresh_service_from_github


class Command(BaseCommand):
    def add_arguments(self, parser):
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
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Print out less.",
        )

    def handle(self, *args, **options):
        quiet = options.get("quiet", False)

        if not options.get("source") and not options.get("all"):
            raise ValueError("Either `--source` or `--all` must be set.")

        if options.get("all"):
            queryset = models.Source.objects.filter(active=True)

        if options.get("source"):
            queryset = models.Source.objects.filter(slug=options.get("source"))

        for source in queryset:
            refresh_service_from_github.delay(source.slug)

        if not quiet:
            print(f"Processed {queryset.count()} sources.")
