import logging

from django.contrib import messages
from django.test import TestCase
from faker import Faker

from services import forms
from services.tests import create_source
from catalog.helpers.tests import WithUser

from .management.commands import truncate
from .models import SystemLog, add_log
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from django.urls import reverse
logging.getLogger("faker").setLevel(logging.ERROR)
fake = Faker("en_US")

class WithSource(WithUser):
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
        add_log(self.source, messages.ERROR, "test")
        self.command(ago=1)
        self.assertEqual(SystemLog.objects.count(), 1)

    def test_truncates(self):
        add_log(self.source, messages.ERROR, "test")
        self.command(ago=0)
        self.assertEqual(SystemLog.objects.count(), 0)


class TestAPI(WithSource):
    def setUp(self):
        super().setUp()
        self.log = add_log(self.source, messages.ERROR, "test")
        self.list_url = reverse("systemlogs:api-list")
        self.detail_url = reverse("systemlogs:api-detail", kwargs={"pk": self.log.pk})

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
        self.assertEqual(response.json()["message"], "test")