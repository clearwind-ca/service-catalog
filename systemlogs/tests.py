import logging

from django.contrib import messages
from django.test import TestCase
from faker import Faker

from services import forms

from .management.commands import truncate
from .models import SystemLog, add_log

logging.getLogger("faker").setLevel(logging.ERROR)
fake = Faker("en_US")


class TestTruncate(TestCase):
    def setUp(self):
        super().setUp()
        self.source = forms.SourceForm(
            {"url": f"https://github.com/{fake.user_name()}/{fake.user_name()}"}
        ).save()
        self.command = truncate.Command().handle

    def test_truncate_fails_with_no_ago(self):
        self.assertRaises(ValueError, self.command)

    def test_truncate_ignores_newer_logs(self):
        add_log(self.source, messages.ERROR, "test")
        self.command(ago=1)
        self.assertEqual(SystemLog.objects.count(), 1)

    def test_truncates(self):
        add_log(self.source, messages.ERROR, "test")
        self.command(ago=0)
        self.assertEqual(SystemLog.objects.count(), 0)
