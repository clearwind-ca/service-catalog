import sys


from django.core.management.base import BaseCommand
from health.tasks import timeout


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--ago",
            type=int,
            help="Mark as timed out, check results older than this in hours",
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
                "Ago is required, use `--ago` to set the number of hours to mark as timed out."
            )

        if ago == 0 and not quiet:
            print("Ago is set to 0, so no check results will timeout.")
            sys.exit(1)

        timeout.delay(ago)

        if not quiet:
            print(f"Queued timing out check results, older than {ago} hours.")
