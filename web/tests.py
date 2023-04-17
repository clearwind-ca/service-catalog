from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from systemlogs.models import SystemLog

from .helpers import process_query_params
from .templatetags.helpers import (apply_format, log_level_as_text,
                                   markdown_filter, priority_as_colour, qs,
                                   strip_format)


class TestProcessQueryParams(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _test_decorator(self, params, expected):
        @process_query_params
        def test(request, query_params=None):
            return query_params

        request = self.factory.get(f"/?{params}")
        test(request)
        if expected is None:
            self.assertIsNone(request.GET)
        else:
            for k, v in expected.items():
                self.assertEqual(request.GET[k], v)

    def test_process_query_params(self):
        """Test the process query params decorator works."""
        self._test_decorator("", {"per_page": 10, "page": 1})
        self._test_decorator("per_page=89&page=2", {"per_page": 89, "page": 2})
        self._test_decorator("per_page=102&page=3", {"per_page": 100, "page": 3})
        self._test_decorator("per_page=foo&page=bar", {"per_page": 10, "page": 1})
        self._test_decorator("active=yes", {"active": True})
        self._test_decorator("active=no", {"active": False})
        self._test_decorator("active=whatever", {"active": None})


class TestHomePage(TestCase):
    def test_home_page(self):
        """Test the home page loads."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")


class TestColour(TestCase):
    def test_colour_filter(self):
        self.assertEqual(priority_as_colour(1), "warning")
        self.assertEqual(priority_as_colour("foo"), "dark")

    def test_log_level_filter(self):
        self.assertEqual(log_level_as_text(20), "Info")


class TestMarkdown(TestCase):
    def test_markdown_filter(self):
        self.assertEqual(markdown_filter("# Hello"), "<h1>Hello</h1>")


class TestQs(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _test_qs(self, params, **overrides):
        request = self.factory.get(f"/?{params}")

        @process_query_params
        def test(request, query_params=None):
            return query_params

        test(request)
        return qs(request, **overrides)

    def test_qs(self):
        self.assertEqual(self._test_qs(""), "?")
        # Irrelevant params are ignored.
        self.assertEqual(self._test_qs("foo=bar"), "?")
        self.assertEqual(self._test_qs("page=10"), "?page=10")
        # Override params works.
        self.assertEqual(self._test_qs("page=10", page=3), "?page=3")
        # Preserve other params.
        self.assertEqual(
            self._test_qs("page=10&active=yes", page=3), "?page=3&active=yes"
        )
        self.assertEqual(self._test_qs("priority=1"), "?priority=1")
        self.assertEqual(self._test_qs("level=10"), "?level=10")
        # No is False and then converted back to no.
        self.assertEqual(self._test_qs("active=no"), "?active=no")
        # Something that converts to None is ignored
        self.assertEqual(self._test_qs("page=10&active=whatever"), "?page=10")


class TestFormat(TestCase):
    def test_strip_format(self):
        for value, expectation in (
            ("foo", "Foo"),
            ("foo_url", "Foo"),
            ("foo_foo_md", "Foo Foo"),
            ("url", "Url"),
        ):
            self.assertEqual(strip_format(value), expectation)

    def test_apply_format(self):
        for value, field, expectation in (
            ("foo", "bar", "foo"),
            ("http://f.com", "f_url", '<a href="http://f.com">http://f.com</a>'),
            ("* foo", "foo_foo_md", "<ul>\n<li>foo</li>\n</ul>"),
            ("http://foo.com", "url", '<a href="http://foo.com">http://foo.com</a>'),
        ):
            self.assertEqual(apply_format(value, field), expectation)


from django.contrib.auth import get_user_model


class TestAPIToken(TestCase):
    def test_api_token(self):
        """Test the API token pages require login."""
        response = self.client.get(reverse("web:api"))
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse("web:api-delete"))
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse("web:api-create"))
        self.assertEqual(response.status_code, 302)

    def add_user(self):
        self.user = get_user_model().objects.create_user(username="andy")

    def test_api_token(self):
        """Test the API token page loads."""
        self.add_user()
        self.client.force_login(self.user)
        response = self.client.get(reverse("web:api"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "api.html")

    def test_api_token_create(self):
        """Test that hitting the API token endpoint creates a token."""
        self.add_user()
        self.client.force_login(self.user)
        response = self.client.post(reverse("web:api-create"))
        token = Token.objects.get(user=self.user)
        self.assertContains(response, token.key)
        self.assertEqual(SystemLog.objects.filter(user=self.user).count(), 1)

    def test_api_token_delete(self):
        """Test that hitting the API token endpoint creates a token."""
        self.add_user()
        self.client.force_login(self.user)
        Token.objects.create(user=self.user)
        assert Token.objects.filter(user=self.user).exists()
        response = self.client.post(reverse("web:api-delete"))
        self.assertEquals(Token.objects.filter(user=self.user).exists(), False)
        self.assertEqual(SystemLog.objects.filter(user=self.user).count(), 1)
