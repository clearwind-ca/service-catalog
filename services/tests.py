import logging

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from faker import Faker

from . import forms, models

logging.getLogger("faker").setLevel(logging.ERROR)
fake = Faker("en_US")


def create_source():
    """Create a source."""
    return forms.SourceForm(
        {"name": f"{fake.user_name()}/{fake.user_name()}", "host": "G"}
    ).save()


def create_service(source):
    """Create a service."""
    return models.Service.objects.create(
        name=fake.user_name(),
        description=fake.text(),
        type="application",
        source=source,
    )


class ServiceTestCase(TestCase):
    def test_service(self):
        """Create a service and a source, validate the relationship."""
        source = create_source()
        service = create_service(source)
        self.assertEqual(service.source, source)

    def test_source_validator(self):
        """Validate the source name validator."""
        form = forms.SourceForm({"name": "ownername", "host": "G"})
        self.assertFalse(form.is_valid())
        assert "name" in form.errors

        form = forms.SourceForm({"name": "owner/name", "host": "G"})
        self.assertTrue(form.is_valid(), form.errors)


class Views(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="andy")
        return super().setUp()

    def test_no_services(self):
        """Test the list services view with no services."""
        self.client.force_login(self.user)
        response = self.client.get("/services/")
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
    def test_service_dependencies(self):
        """Test that dependencies are not symmetrical."""
        source = create_source()
        service_parent = create_service(source)
        service_child = create_service(source)
        service_parent.dependencies.add(service_child)
        self.assertEqual(service_parent.dependencies.first(), service_child)
        self.assertEqual(service_child.dependencies.count(), 0)
