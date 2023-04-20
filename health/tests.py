from django.urls import reverse

from catalog.helpers.tests import WithUser
from services.tests import create_service, create_source
import os
from unittest.mock import patch
from .models import Check, CheckResult
from .management.commands import send 
from django.contrib.auth.models import User
from faker import Faker
fake = Faker()

def create_health_check():
    source = create_source()
    service = create_service(source)
    health_check = Check.objects.create(name=fake.name())
    return {"source": source, "service": service, "health_check": health_check}


def create_health_check_result(health_check, service):
    return CheckResult.objects.create(
        health_check=health_check,
        service=service,
    )

class WithHealthCheck(WithUser):
    def setUp(self):
        super().setUp()
        created = create_health_check()
        self.source = created["source"]
        self.service = created["service"]
        self.health_check = created["health_check"]

class TestAPICheck(WithUser):
    def setUp(self):
        super().setUp()
        self.source = create_source()
        self.service = create_service(self.source)
    
    def test_add_check(self):
        """Tests adding in a check via the API"""
        url = reverse("health:api-check-list")
        data = {
            "name": fake.name(),
            "active": True,
        }
        self.api_login()
        response = self.api_client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(Check.objects.get().name, data["name"])

    def test_change_check(self):
        """Tests editing a check via the API"""
        original = "some name"
        check = Check.objects.create(name=original)
        url = reverse("health:api-check-detail", args=[check.pk])
        data = {
            "name": "some other name",
            "active": False,
        }
        self.api_login()
        response = self.api_client.patch(url, data, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        check = Check.objects.first()
        # Slug hasn't changed.
        self.assertEqual(check.slug, "some-name")
        self.assertEqual(check.active, False)
    
    def test_delete_check(self):
        """Test deleting via the API also deletes results"""
        check = Check.objects.create(name=fake.name())
        CheckResult.objects.create(health_check=check, service=self.service)

        url = reverse("health:api-check-detail", args=[check.pk])
        self.api_login()
        response = self.api_client.delete(url, format="json")
        self.assertEqual(response.status_code, 204, response.content)
        self.assertEqual(Check.objects.count(), 0)
        self.assertEqual(CheckResult.objects.count(), 0)


class TestAPIResult(WithHealthCheck):
    def test_add_result(self):
        url = reverse("health:api-result-list")
        data = {
            "service": self.service.pk,
            "result": "pass",
            "message": "Test message",
            "health_check": self.health_check.pk,
        }
        self.api_login()
        response = self.api_client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(CheckResult.objects.count(), 1)
        self.assertEqual(CheckResult.objects.get().message, "Test message")

    def test_patch_result(self):
        result = create_health_check_result(self.health_check, self.service)
        url = reverse("health:api-result-detail", args=[result.pk])
        data = {
            "result": "pass",
        }
        self.api_login()
        response = self.api_client.patch(url, data, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(CheckResult.objects.first().result, "pass")


class TestSend(WithHealthCheck):
    def setUp(self):
        super().setUp()
        self.command = send.Command().handle

    def test_arg_combos_fails(self):
        for params in [
            {"user": None},
            {"all_checks": False, "check": False, "user": self.user.username},
            {"all_services": False, "service": False, "user": self.user.username},
            ]:
            with self.assertRaises(ValueError):
                self.command(**params)
    
    def test_no_user(self):
        """Takes the username from the environment, and checks it fails"""
        os.environ["CRON_USER"] = "nope"
        self.assertRaises(User.DoesNotExist, self.command)
        del os.environ["CRON_USER"]

    def test_refresh_fails_with_wrong_command_user(self):
        """Test the username from the command, and checks it fails"""
        self.assertRaises(User.DoesNotExist, self.command, user="nope")
 
    @patch("health.management.commands.send.send")
    def test_send_one(self, mock_send):
        """Test sends one"""
        mock_send.dispatch.return_value = True
        kwargs = {"all_checks": True, "all_services": True, "user": self.user.username, "quiet": True}
        with self.settings(SEND_CHECKS_DELAY=0):
            self.command(**kwargs)
        # 1 Service and 1 Check Result
        self.assertEqual(mock_send.dispatch.call_count, 1)
        result = CheckResult.objects.get()
        self.assertEqual(result.status, "sent")
        self.assertEqual(result.result, "unknown")
