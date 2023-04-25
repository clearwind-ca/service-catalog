import os
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from faker import Faker

from catalog.errors import NoRepository
from catalog.helpers.tests import WithUser
from services.tests import create_service, create_source

from .management.commands import send, timeout
from .models import Check, CheckResult

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
        if "CRON_USER" in os.environ:
            del os.environ["CRON_USER"]

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
    def test_logs_and_stops(self, mock_send):
        """A fatal error stops the process"""
        Check.objects.create(name=fake.name())
        mock_send.dispatch.side_effect = NoRepository("Nope")
        kwargs = {
            "all_checks": True,
            "all_services": True,
            "user": self.user.username,
            "quiet": True,
        }
        with self.settings(SEND_CHECKS_DELAY=0):
            self.assertRaises(NoRepository, self.command, **kwargs)
        self.assertEqual(mock_send.dispatch.call_count, 1)
        result = CheckResult.objects.get()
        self.assertEqual(result.status, "error")

    @patch("health.management.commands.send.send")
    def test_send_one(self, mock_send):
        """Test sends one"""
        Check.objects.create(name=fake.name())
        mock_send.dispatch.return_value = True
        kwargs = {
            "all_checks": True,
            "all_services": True,
            "user": self.user.username,
            "quiet": True,
        }
        with self.settings(SEND_CHECKS_DELAY=0):
            self.command(**kwargs)
        # 1 Service and 2 Checks, means 2 calls.
        self.assertEqual(mock_send.dispatch.call_count, 2)
        self.assertEqual(CheckResult.objects.count(), 2)
        for result in CheckResult.objects.all():
            self.assertEqual(result.status, "sent")
            self.assertEqual(result.result, "unknown")


class TestResultModel(WithHealthCheck):
    def test_health_result_logic(self):
        result = create_health_check_result(self.health_check, self.service)
        self.assertEqual(result.status, "sent")
        result.result = "pass"
        result.save()
        self.assertEqual(result.status, "completed")
        result.result = "fail"
        self.assertRaises(ValueError, result.save)


class TestTimeout(WithHealthCheck):
    def setUp(self):
        super().setUp()
        self.command = timeout.Command().handle

    def test_timeout(self):
        """Timeouts a check"""
        create_health_check_result(self.health_check, self.service)
        # Set the result to be 12 hours old.
        CheckResult.objects.update(updated=timezone.now() - timedelta(hours=12))

        # This times out things older than 13 hours.
        self.command(quiet=True, ago=13)
        self.assertEquals(CheckResult.objects.filter(status="sent").count(), 1)

        # This times out things older than 11 hours, our check result.
        self.command(quiet=True, ago=11)
        self.assertEquals(CheckResult.objects.filter(status="timed-out").count(), 1)


class TestAdHoc(WithHealthCheck):
    def setUp(self):
        super().setUp()
        self.url = reverse("health:checks-run", args=[self.health_check.slug])

    def test_get(self):
        """Test the view fails if a GET"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    @patch("health.views.send")
    def test_post(self, mock_send):
        """Test the view works if a POST"""
        mock_send.dispatch.return_value = True
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CheckResult.objects.filter(status="sent").count(), 1)

    @patch("health.views.send")
    def test_post(self, mock_send):
        """Test the view works if a POST"""
        mock_send.dispatch.side_effect = NoRepository("Nope")
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CheckResult.objects.filter(status="error").count(), 1)

    @patch("health.views.send")
    def test_api_post(self, mock_send):
        """Test the view works if as a POST in the API"""
        self.url = reverse("health:api-checks-run", args=[self.health_check.pk])
        self.api_login()
        response = self.api_client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CheckResult.objects.filter(status="sent").count(), 1)

    @patch("health.views.send")
    def test_api_post(self, mock_send):
        """Test the view fails if as an anonymous POST in the API"""
        self.url = reverse("health:api-checks-run", args=[self.health_check.pk])
        response = self.api_client.post(self.url)
        self.assertEqual(response.status_code, 401)
