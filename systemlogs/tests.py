from auditlog.models import LogEntry
from django.urls import reverse
from faker import Faker

from catalog.tests import BaseTestCase
from services.tests import create_source

from .management.commands import truncate

fake = Faker("en_US")


class WithSource(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.source = create_source()


class TestTruncate(WithSource):
    def setUp(self):
        super().setUp()
        self.command = truncate.Command().handle

    def test_truncate_fails_with_no_ago(self):
        self.assertRaises(ValueError, self.command)

    def test_truncate_ignores_newer_logs(self):
        entries = LogEntry.objects.count()
        with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
            self.command(ago=1, quiet=True)
        self.assertEqual(LogEntry.objects.count(), entries)

    def test_truncates(self):
        LogEntry.objects.log_create(self.source)
        with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
            self.command(ago=0, quiet=True)
        self.assertEqual(LogEntry.objects.count(), 0)


class TestAPI(WithSource):
    def setUp(self):
        super().setUp()
        LogEntry.objects.log_create(self.source, force_log=True)
        self.log = LogEntry.objects.all().first()
        self.list_url = reverse("logs:api-list")
        self.detail_url = reverse("logs:api-detail", kwargs={"pk": self.log.pk})

    def test_logs_list_unauth(self):
        response = self.api_client.get(self.list_url)
        self.assertEqual(response.status_code, 401)

    def test_logs_list_auth(self):
        self.api_login()
        response = self.api_client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

    def test_logs_detail_unauth(self):
        response = self.api_client.get(self.detail_url)
        self.assertEqual(response.status_code, 401)

    def test_logs_detail_auth(self):
        self.api_login()
        response = self.api_client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["object_repr"], self.source.slug)
