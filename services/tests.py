import os
from unittest.mock import patch

from auditlog.models import LogEntry
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models.deletion import ProtectedError
from django.forms.models import model_to_dict
from django.test import TestCase
from django.urls import reverse
from faker import Faker

from catalog.errors import FetchError
from catalog.helpers.tests import WithUser
from web.shortcuts import get_object_or_None

from . import forms, models
from .management.commands.refresh import Command

fake = Faker("en_US")


def create_source():
    """Create a source."""
    return forms.SourceForm(
        {"url": f"https://github.com/{fake.user_name()}/{fake.user_name()}", "active": True}
    ).save()


def create_service(source):
    """Create a service."""
    return models.Service.objects.create(
        name=fake.user_name(),
        description=fake.text(),
        type="application",
        source=source,
        meta={"foo": "bar"},
        events=["deployments"]
    )


def sample_response():
    return [
        {
            "contents": {
                "priority": 1,
                "name": "test-gh",
                "type": "application",
                "description": "test",
            }
        }
    ]


def mixed_responses():
    return [
        {
            "contents": {
                "priority": 1,
                "name": fake.user_name(),
                "type": "application",
                "description": fake.text(),
            }
        },
        {
            "contents": {
                "name": fake.user_name(),
                "type": "application",
                "description": fake.text(),
            }
        },
        {
            "contents": {
                "name": fake.user_name(),
                "priority": 12,
                "description": fake.text(),
            }
        },
    ]


class ServiceTestCase(TestCase):
    def test_service(self):
        """Create a service and a source, validate the relationship."""
        source = create_source()
        service = create_service(source)
        self.assertEqual(service.source, source)

    def test_source_validator(self):
        """Validate the source name validator."""
        form = forms.SourceForm({"url": "something"})
        self.assertFalse(form.is_valid())
        assert "url" in form.errors

        form = forms.SourceForm({"url": "https://github.com/gh/gh"})
        self.assertTrue(form.is_valid(), form.errors)


class TestServiceList(WithUser):
    def test_no_services(self):
        """Test the list services view with no services."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("services:service-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blankslate.html")

    def test_not_logged_in(self):
        """Test the list services view when not logged in."""
        response = self.client.get(reverse("services:service-list"))
        self.assertEqual(response.status_code, 302)

    def test_a_service(self):
        """Test the list services view with a service."""
        self.client.force_login(self.user)
        source = create_source()
        service = create_service(source)
        response = self.client.get(reverse("services:service-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "service-list.html")
        self.assertContains(response, service.name)
        self.assertContains(response, service.type)

    def test_get_service_not_logged_in(self):
        """Test the page for viewing a service when not logged in."""
        source = create_source()
        service = create_service(source)
        response = self.client.get(
            reverse("services:service-detail", kwargs={"slug": service.slug})
        )
        self.assertEqual(response.status_code, 302)

    def test_get_service(self):
        """Test the page for viewing a service."""
        self.client.force_login(self.user)
        source = create_source()
        service = create_service(source)
        response = self.client.get(
            reverse("services:service-detail", kwargs={"slug": service.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "service-detail.html")


class TestDependencies(TestCase):
    def setUp(self):
        self.source = create_source()
        self.service_parent = create_service(self.source)

    def get_service_stub(self):
        return {
            "name": fake.user_name(),
            "description": fake.text(),
            "priority": 1,
            "type": "application",
        }

    def test_service_dependencies(self):
        """Test that dependencies are not symmetrical."""
        service_child = create_service(self.source)
        self.service_parent.dependencies.add(service_child)
        self.assertEqual(self.service_parent.dependencies.first(), service_child)
        self.assertEqual(service_child.dependencies.count(), 0)
        self.assertEqual(service_child.dependents().count(), 1)

    def process_form(self, service_stub):
        form = forms.ServiceForm({"data": service_stub})
        form.source = self.source
        assert form.is_valid(), form.errors
        return form.save()

    def test_create_service_adds_dependencies(self):
        """Test that create services adds dependencies."""
        service_stub = self.get_service_stub()
        service_stub["dependencies"] = [self.service_parent.slug]
        result = self.process_form(service_stub)
        assert result["created"]
        self.assertEqual(result["service"].dependencies.first(), self.service_parent)

    def test_update_service_adds_dependencies(self):
        """Test that updating a service adds dependencies."""
        service_stub = self.get_service_stub()
        result = self.process_form(service_stub)
        assert result["created"]
        self.assertEqual(result["service"].dependencies.first(), None)

        service_stub["dependencies"] = [self.service_parent.slug]
        result = self.process_form(service_stub)
        assert result["created"] == False
        self.assertEqual(result["service"].dependencies.first(), self.service_parent)

    def test_update_service_does_not_add_incorrect_dependencies(self):
        """Test that updating a service does not add an invalid dependency."""
        service_stub = self.get_service_stub()
        result = self.process_form(service_stub)
        assert result["created"]
        self.assertEqual(result["service"].dependencies.first(), None)

        service_stub["dependencies"] = ["not-a-slug"]
        result = self.process_form(service_stub)
        assert result["created"] == False
        self.assertEqual(result["service"].dependencies.first(), None)

    def test_update_service_removes_dependencies(self):
        """Test that updating a service removes dependencies."""
        service_stub = self.get_service_stub()
        service_stub["dependencies"] = [self.service_parent.slug]
        result = self.process_form(service_stub)
        assert result["created"]
        self.assertEqual(result["service"].dependencies.first(), self.service_parent)

        service_stub["dependencies"] = []
        result = self.process_form(service_stub)
        assert result["created"] == False
        self.assertEqual(result["service"].dependencies.first(), None)

    def test_update_service_keeps_dependencies(self):
        """Test that updating a service keep dependencies."""
        service_stub = self.get_service_stub()
        service_stub["dependencies"] = [self.service_parent.slug]
        result = self.process_form(service_stub)
        assert result["created"]
        self.assertEqual(result["service"].dependencies.first(), self.service_parent)

        result = self.process_form(service_stub)
        assert result["created"] == False
        self.assertEqual(result["service"].dependencies.first(), self.service_parent)


class TestSchema(WithUser):
    def test_schema(self):
        """Test the list schema view."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("services:schema-detail"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "schema-detail.html")

    def test_not_logged_in(self):
        """Test the list schema view when not logged in."""
        response = self.client.get(reverse("services:schema-detail"))
        self.assertEqual(response.status_code, 302)


class TestValidate(WithUser):
    def setUp(self):
        super().setUp()
        self.source = create_source()
        self.url = reverse("services:source-validate", kwargs={"slug": self.source.slug})

    def test_not_logged_in(self):
        """Test the list schema view when not logged in."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    @patch("services.views.fetch")
    def test_validate_bad_json(self, mock_fetch):
        """Test the validate sources view with some non-schema JSON."""
        self.client.force_login(self.user)
        mock_fetch.get.return_value = [{"contents": {"hi": "there"}}]
        response = self.client.get(self.url)
        self.assertEqual(self.get_message(response).level, messages.ERROR)

    @patch("services.views.fetch")
    def test_validate_invalid_json(self, mock_fetch):
        """Test the validate sources view with some totally invalid JSON."""
        self.client.force_login(self.user)
        mock_fetch.get.return_value = [{"contents": 1}]
        response = self.client.get(self.url)
        self.assertEqual(self.get_message(response).level, messages.ERROR)

    @patch("services.views.fetch")
    def test_validate_good_json(self, mock_fetch):
        """Test the validate sources view."""
        self.client.force_login(self.user)
        mock_fetch.get.return_value = [
            {
                "contents": {
                    "priority": 1,
                    "name": "test",
                    "type": "application",
                    "description": "test",
                }
            }
        ]
        response = self.client.get(self.url)
        self.assertEqual(self.get_message(response).level, messages.INFO)


class TestDelete(WithUser):
    def setUp(self):
        super().setUp()
        self.source = create_source()
        self.url = reverse("services:source-delete", kwargs={"slug": self.source.slug})

    def test_not_logged_in(self):
        """Test the list schema view when not logged in."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_not_post(self):
        """Test the delete source view fails if a GET"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_delete_works(self):
        """Test the delete source view."""
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(self.get_message(response).level, messages.INFO)
        assert not models.Source.objects.filter(slug=self.source.slug).exists()

    def test_delete_stops(self):
        """Test the delete source view stops if there are services."""
        self.client.force_login(self.user)
        create_service(self.source)
        response = self.client.post(self.url)
        self.assertEqual(self.get_message(response).level, messages.ERROR)
        assert models.Source.objects.filter(slug=self.source.slug).exists()

    def test_delete_still_has_log(self):
        """Test that we've still got the system log entries."""
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(self.get_message(response).level, messages.INFO)
        # Assert that we still have the system log entries for that object.
        self.assertEquals(LogEntry.objects.get_for_object(self.source).exists(), True)


class TestAdd(WithUser):
    def setUp(self):
        super().setUp()
        self.url = reverse("services:source-add")

    def test_not_logged_in(self):
        """Test the source add view when not logged in."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_get(self):
        """Test the source add view."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "source-add.html")

    @patch("services.views.fetch")
    def test_post(self, mock_fetch):
        """Test the source add view with a POST."""
        self.client.force_login(self.user)
        mock_fetch.get.return_value = sample_response()
        response = self.client.post(self.url, {"url": "https://gh.com/andy/gh"})
        self.assertEqual(self.get_message(response).level, messages.INFO)
        assert models.Source.objects.filter(slug="andy-gh").exists()

    def test_post_errors(self):
        """Test the source add view with a POST that errors"""
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"url": "sort-of-failure"})
        self.assertEqual(self.get_message(response).level, messages.ERROR)
        assert not models.Source.objects.filter(slug="andy-gh").exists()


class TestSourceList(WithUser):
    def setUp(self):
        super().setUp()
        self.url = reverse("services:source-list")

    def test_not_logged_in(self):
        """Test the source list view when not logged in."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_logged_in_empty(self):
        """Test the source list view when logged in, but no sources."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "source-list.html")
        self.assertEqual(len(response.context["sources"]), 0)

    def test_logged_in_with_a_source(self):
        """Test the source list view when logged in, and a source."""
        self.client.force_login(self.user)
        create_source()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "source-list.html")
        self.assertEqual(len(response.context["sources"]), 1)


class TestServiceDetail(WithUser):
    def setUp(self):
        super().setUp()
        self.source = create_source()
        self.service = create_service(self.source)
        self.url = reverse("services:service-detail", kwargs={"slug": self.service.slug})

    def test_not_logged_in(self):
        """Test the service detail view when not logged in."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_logged_in(self):
        """Test the service detail view when logged in."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "service-detail.html")
        self.assertEqual(response.context["service"], self.service)


class TestServiceDelete(WithUser):
    def setUp(self):
        super().setUp()
        self.source = create_source()
        self.service = create_service(self.source)
        self.url = reverse("services:service-delete", kwargs={"slug": self.service.slug})

    def test_not_logged_in(self):
        """Test the service delete view when not logged in."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_not_post(self):
        """Test the service delete view fails if a GET"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_delete_works(self):
        """Test the delete service view."""
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(self.get_message(response).level, messages.INFO)
        assert not models.Service.objects.filter(slug=self.service.slug).exists()


class TestManagementRefresh(WithUser):
    def setUp(self):
        super().setUp()
        self.command = Command()

    def test_refresh_fails_with_no_user(self):
        """Test the refresh command fails with no user"""
        self.assertRaises(ValueError, self.command.handle)

    def test_refresh_fails_with_wrong_cron_user(self):
        """Takes the username from the environment, and checks it fails"""
        os.environ["CRON_USER"] = "nope"
        self.assertRaises(User.DoesNotExist, self.command.handle)
        del os.environ["CRON_USER"]

    def test_refresh_fails_with_wrong_command_user(self):
        """Test the username from the command, and checks it fails"""
        self.assertRaises(User.DoesNotExist, self.command.handle, user="nope")

    def test_refresh_fails_with_no_source(self):
        """Test fails if no source"""
        self.assertRaises(ValueError, self.command.handle, user=self.user.username)

    @patch("services.tasks.fetch")
    def test_refresh_all(self, mock_fetch):
        """Test refreshes all"""
        create_source()
        create_source()
        mock_fetch.get.return_value = sample_response()
        with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
            self.command.handle(user=self.user.username, all=True, quiet=True)
        self.assertEquals(models.Service.objects.all().count(), 1)
        self.assertEquals(mock_fetch.get.call_count, 2)

    @patch("services.tasks.fetch")
    def test_refresh_some(self, mock_fetch):
        """Test refreshes some"""
        create_source()  # Will not be refreshed.
        second = create_source()  # Will be refreshed.
        mock_fetch.get.return_value = sample_response()
        with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
            self.command.handle(user=self.user.username, source=second.slug, quiet=True)
        self.assertEquals(models.Service.objects.all().count(), 1)
        self.assertEquals(mock_fetch.get.call_count, 1)

    @patch("services.tasks.fetch")
    def test_refresh_active_only(self, mock_fetch):
        """Test refreshes all"""
        source = create_source()
        source.active = False
        source.save()

        mock_fetch.get.return_value = sample_response()
        with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
            self.command.handle(user=self.user.username, all=True, quiet=True)

        self.assertEquals(mock_fetch.get.call_count, 0)


class TestServiceForm(WithUser):
    def setUp(self):
        super().setUp()

    def test_form_update(self):
        """Object updated if something changed."""
        source = create_source()
        service = create_service(source)
        data = model_to_dict(service)
        data["description"] = fake.text()
        form = forms.ServiceForm(data={"data": data})
        form.source = source
        self.assertTrue(form.is_valid(), form.errors)
        assert form.save()["updated"]

    def test_form_ignores_update(self):
        """Object not updated if nothing changed."""
        source = create_source()
        service = create_service(source)
        data = model_to_dict(service)
        form = forms.ServiceForm(data={"data": data})
        form.source = source
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save()["updated"], False)


class TestAPISource(WithUser):
    def setUp(self):
        super().setUp()
        self.source_list = reverse("services:api-source-list")

    def test_source_list(self):
        """Test the source list API."""
        self.api_login()
        response = self.api_client.get(self.source_list)
        self.assertEqual(response.status_code, 200)

    def test_source_unauth(self):
        """Test the source list API as an unauthed user."""
        response = self.api_client.get(self.source_list)
        self.assertEqual(response.status_code, 401)

    def test_source_delete(self):
        """Test deleting a source."""
        self.api_login()
        self.source = create_source()
        url = reverse("services:api-source-detail", kwargs={"pk": self.source.pk})
        response = self.api_client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(get_object_or_None(models.Source, pk=self.source.pk), None)

    def test_source_delete(self):
        """Test deleting a source with a service."""
        self.api_login()
        self.source = create_source()
        self.service = create_service(self.source)
        url = reverse("services:api-source-detail", kwargs={"pk": self.source.pk})
        self.assertRaises(ProtectedError, self.api_client.delete, url)

    def test_source_add_and_get(self):
        """Test the source list API as POST"""
        self.api_login()
        fake_url = fake.url()
        response = self.api_client.post(self.source_list, data={"url": fake_url})
        self.assertEqual(response.status_code, 201)

        url = reverse("services:api-source-detail", kwargs={"pk": response.data["id"]})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["url"], fake_url)

    def test_refresh_unauth(self):
        """Test the source validate API requires auth."""
        self.source = create_source()
        url = reverse("services:api-source-refresh", kwargs={"pk": self.source.pk})
        response = self.api_client.post(url)
        self.assertEqual(response.status_code, 401)

    @patch("services.views.fetch")
    def test_source_add_and_refresh(self, mock_fetch):
        """Test the source list API as POST"""
        self.source = create_source()
        self.api_login()
        url = reverse("services:api-source-refresh", kwargs={"pk": self.source.pk})
        mock_fetch.get.return_value = sample_response()
        response = self.api_client.post(url)
        assert mock_fetch.get.called
        self.assertEqual(response.status_code, 200)

    @patch("services.views.fetch")
    def test_validate_gateway_error(self, mock_fetch):
        """Test the source validate API when it fails on fetch."""
        self.source = create_source()
        self.api_login()
        url = reverse("services:api-source-validate", kwargs={"pk": self.source.pk})
        mock_fetch.get.side_effect = FetchError("Nope")
        response = self.api_client.post(url)
        assert mock_fetch.get.called
        self.assertEqual(response.status_code, 502)

    def test_validate_unauth(self):
        """Test the source validate API requires auth."""
        self.source = create_source()
        url = reverse("services:api-source-validate", kwargs={"pk": self.source.pk})
        response = self.api_client.post(url)
        self.assertEqual(response.status_code, 401)

    @patch("services.views.fetch")
    def test_validate_error(self, mock_fetch):
        """Test the source validate API when it fails on a record."""
        self.source = create_source()
        self.api_login()
        url = reverse("services:api-source-validate", kwargs={"pk": self.source.pk})
        # Will return multiple errors and one success.
        mock_fetch.get.return_value = mixed_responses()
        response = self.api_client.post(url)
        assert mock_fetch.get.called
        self.assertEqual(response.status_code, 502)
        self.assertEqual(len(response.json()["failures"]), 2)
        first = response.json()["failures"][0]
        assert "priority" in first["data"][0]["message"]
        second = response.json()["failures"][1]
        assert "type" in second["data"][0]["message"]


class TestAPIService(WithUser):
    def setUp(self):
        super().setUp()
        self.service_list = reverse("services:api-service-list")

    def test_service_list(self):
        """Test the service list API."""
        self.api_login()
        response = self.api_client.get(self.service_list)
        self.assertEqual(response.status_code, 200)

    def test_service_unauth(self):
        """Test the service list API as an unauthed user."""
        response = self.api_client.get(self.service_list)
        self.assertEqual(response.status_code, 401)

    def test_service_get(self):
        """Test the service list API as GET"""
        self.api_login()
        self.source = create_source()
        self.service = create_service(self.source)
        url = reverse("services:api-service-detail", kwargs={"pk": self.service.pk})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["description"], self.service.description)

    def test_service_delete(self):
        """Test deleting a service."""
        self.api_login()
        self.source = create_source()
        self.service = create_service(self.source)
        url = reverse("services:api-service-detail", kwargs={"pk": self.service.pk})
        response = self.api_client.delete(url)
        self.assertEqual(response.status_code, 204, response.content)
        self.assertEqual(get_object_or_None(models.Service, pk=self.service.pk), None)


class TestAPIService(WithUser):
    def test_get_schema(self):
        self.url = reverse("services:api-schema-detail")
        response = self.api_client.get(self.url)
        self.assertEqual(response.status_code, 200)
