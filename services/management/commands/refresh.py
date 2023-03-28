from django.core.management.base import BaseCommand

from services.models import Source


class Command(BaseCommand):
    def handle(self, *args, **options):
        for source in Source.objects.all():
            source.refresh()
