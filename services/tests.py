import logging
import os
from unittest.mock import patch

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from faker import Faker

from . import forms, models
from .management.commands.refresh import Command, UserError

logging.getLogger("faker").setLevel(logging.ERROR)
fake = Faker("en_US")


def create_source():
    """Create a source."""
    return forms.SourceForm(
        {"url": f"https://github.com/{fake.user_name()}/{fake.user_name()}"}
    ).save()


def create_service(source):
    """Create a service."""
    return models.Service.objects.create(
        name=fake.user_name(),
        description=fake.text(),
        type="application",
        source=source,
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


class WithUser(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="andy")
        return super().setUp()

    def get_messages(self, response):
        """Get the messages from the response."""
        return list(messages.get_messages(response.wsgi_request))

    def get_message(self, response):
        """Get the first message from the response."""
        return self.get_messages(response)[0]


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
        response = self.client.get(reverse("services:service_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blankslate.html")

    def test_not_logged_in(self):
        """Test the list services view when not logged in."""
        response = self.client.get(reverse("services:service_list"))
        self.assertEqual(response.status_code, 302)

    def test_a_service(self):
        """Test the list services view with a service."""
        self.client.force_login(self.user)
        source = create_source()
        service = create_service(source)
        response = self.client.get(reverse("services:service_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "service-list.html")
        self.assertContains(response, service.name)
        self.assertContains(response, service.type)

    def test_get_service_not_logged_in(self):
        """Test the page for viewing a service when not logged in."""
        source = create_source()
        service = create_service(source)
        response = self.client.get(
            reverse("services:service_detail", kwargs={"slug": service.slug})
        )
        self.assertEqual(response.status_code, 302)

    def test_get_service(self):
        """Test the page for viewing a service."""
        self.client.force_login(self.user)
        source = create_source()
        service = create_service(source)
        response = self.client.get(
            reverse("services:service_detail", kwargs={"slug": service.slug})
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
        """Test that updating a service adds dependencies."""
        service_stub = self.get_service_stub()
        result = self.process_form(service_stub)
        assert result["created"]
        self.assertEqual(result["service"].dependencies.first(), None)

        service_stub["dependencies"] = ["not-a-slug"]
        result = self.process_form(service_stub)
        assert result["created"] == False
        self.assertEqual(result["service"].dependencies.first(), None)
        assert result["logs"][0].startswith("Updated service"), result["logs"][0]

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
        response = self.client.get(reverse("services:schema_detail"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "schema-detail.html")

    def test_not_logged_in(self):
        """Test the list schema view when not logged in."""
        response = self.client.get(reverse("services:schema_detail"))
        self.assertEqual(response.status_code, 302)


class TestValidate(WithUser):
    def setUp(self):
        super().setUp()
        self.source = create_source()
        self.url = reverse(
            "services:source_validate", kwargs={"slug": self.source.slug}
        )

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
        self.url = reverse("services:source_delete", kwargs={"slug": self.source.slug})

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
        assert self.source.logs().count() > 0


class TestAdd(WithUser):
    def setUp(self):
        super().setUp()
        self.url = reverse("services:source_add")

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
        self.url = reverse("services:source_list")

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
        self.url = reverse(
            "services:service_detail", kwargs={"slug": self.service.slug}
        )

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
        self.url = reverse(
            "services:service_delete", kwargs={"slug": self.service.slug}
        )

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
        self.assertRaises(UserError, self.command.handle)

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

    @patch("services.management.commands.refresh.fetch")
    def test_refresh_all(self, mock_fetch):
        """Test refreshes all"""
        create_source()
        create_source()
        mock_fetch.get.return_value = sample_response()
        sources = self.command.handle(user=self.user.username, all=True)
        assert len(sources["queryset"]) == 2
        assert sources["outputs"][0]["created"]

    @patch("services.management.commands.refresh.fetch")
    def test_refresh_some(self, mock_fetch):
        """Test refreshes some"""
        create_source()  # Will not be refreshed.
        second = create_source()  # Will be refreshed.
        mock_fetch.get.return_value = sample_response()
        sources = self.command.handle(user=self.user.username, source=second.slug)
        assert len(sources["queryset"]) == 1
        assert sources["queryset"][0] == second
