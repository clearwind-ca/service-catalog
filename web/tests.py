from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.urls import reverse
from faker import Faker
from rest_framework.authtoken.models import Token
from django.shortcuts import redirect


from django.contrib.auth import get_user_model
from catalog.tests import BaseTestCase
from services.models import Organization

from .helpers import process_query_params
from .middleware import CatalogMiddleware
from .templatetags.helpers import (
    apply_format,
    markdown_filter,
    priority_as_colour,
    qs,
    strip_format,
    yesno_if_boolean,
)

fake = Faker("en_US")

# Truncated....
example_app_response = {
    "id": fake.random_int(),
    "slug": fake.slug(),
    "node_id": fake.uuid4(),
    "owner": {},
    "name": fake.name(),
    "html_url": "https://github.com/apps/catalog-for-burnt-tomatoes3",
    "created_at": fake.date_time(),
    "updated_at": fake.date_time(),
    "client_id": fake.text(),
    "webhook_secret": None,
    "pem": fake.text(),
    "client_secret": fake.text(),
}


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
        self.assertEqual(response.status_code, 200, response.headers)
        self.assertTemplateUsed(response, "home.html")


class TestColour(TestCase):
    def test_colour_filter(self):
        self.assertEqual(priority_as_colour(1), "warning")
        self.assertEqual(priority_as_colour("foo"), "dark")


class TestMarkdown(TestCase):
    def test_markdown_filter(self):
        self.assertEqual(markdown_filter("# Hello"), "<h1>Hello</h1>")


class TestYesNo(TestCase):
    def test_yesno_filter(self):
        self.assertEqual(yesno_if_boolean(True), "yes")
        self.assertEqual(yesno_if_boolean(False), "no")
        self.assertEqual(yesno_if_boolean(None), None)
        self.assertEqual(yesno_if_boolean("foo"), "foo")


class TestQs(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _test_qs(self, params, *overrides):
        request = self.factory.get(f"/?{params}")

        @process_query_params
        def test(request, query_params=None):
            return query_params

        test(request)
        return qs(request, *overrides)

    def test_qs(self):
        self.assertEqual(self._test_qs("page=10", None, None), "?page=10&active=yes")
        # Override params works.
        self.assertEqual(self._test_qs("page=10", "page", 3), "?page=3&active=yes")
        # Preserve other params.
        self.assertEqual(self._test_qs("page=10&active=yes", "page", 3), "?page=3&active=yes")
        self.assertEqual(self._test_qs("priority=1", None, None), "?active=yes&priority=1")
        self.assertEqual(self._test_qs("level=10", None, None), "?active=yes&level=10")
        # No is False and then converted back to no.
        self.assertEqual(self._test_qs("active=no", None, None), "?active=no")
        self.assertEqual(self._test_qs("active=all", None, None), "?")
        # Something that converts to None is ignored
        self.assertEqual(self._test_qs("page=10&active=whatever", None, None), "?page=10")


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



class TestAPIToken(BaseTestCase):
    def setUp(self):
        super().setUp()
        Token.objects.all().delete()

    def test_api_token(self):
        """Test the API token pages require login."""
        response = self.client.get(reverse("web:api"))
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse("web:api-delete"))
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse("web:api-create"))
        self.assertEqual(response.status_code, 302)

    def test_api_token(self):
        """Test the API token page loads."""
        self.login()
        response = self.client.get(reverse("web:api"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "api.html")

    def test_api_token_create(self):
        """Test that hitting the API token endpoint creates a token."""
        self.login()
        response = self.client.post(reverse("web:api-create"))
        token = Token.objects.get(user=self.user)
        self.assertContains(response, token.key)
        self.assertEquals(Token.objects.filter(user=self.user).exists(), True)

    def test_api_token_delete(self):
        """Test that hitting the API token endpoint deletes a token."""
        self.login()
        Token.objects.create(user=self.user)
        assert Token.objects.filter(user=self.user).exists()
        self.client.post(reverse("web:api-delete"))
        self.assertEquals(Token.objects.filter(user=self.user).exists(), False)


class TestMiddleware(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.req = self.factory.get("/services/")
        self.user = get_user_model().objects.create_user(username="andy")
        self.check_orgs = CatalogMiddleware(Mock()).check_orgs
        self.process_request = CatalogMiddleware(Mock()).process_request
        super().setUp()

    def tearDown(self):
        super().tearDown()
        cache.clear()

    @patch("web.middleware.user")
    def test_orgs_anon_not_member(self, mock_user):
        """
        There are orgs, and the user isnt a member of any of them, but
        the URL has been added to the allow list for anonymous users.
        """
        self.req = self.factory.get("/")
        Organization.objects.create(name="foo")
        self.req.user = self.user
        mock_user.check_org_membership.return_value = False
        self.assertEqual(self.check_orgs(self.req), True)

    def test_no_orgs_anon(self):
        self.req.user = AnonymousUser()
        self.assertEquals(self.check_orgs(self.req), False)

    def test_no_orgs_user(self):
        self.req.user = self.user
        self.assertEquals(self.check_orgs(self.req), False)

    def test_orgs_anon(self):
        Organization.objects.create(name="foo")
        self.req.user = AnonymousUser()
        self.assertEqual(self.check_orgs(self.req), False)

    def test_orgs_anon(self):
        Organization.objects.create(name="foo")
        self.req.user = AnonymousUser()
        self.assertEqual(self.check_orgs(self.req), False)

    @patch("web.middleware.user")
    def test_orgs_not_member(self, mock_user):
        Organization.objects.create(name="foo")
        self.req.user = self.user
        mock_user.check_org_membership.return_value = False
        print(mock_user.check_org_membership())
        self.assertEqual(self.check_orgs(self.req), False)

    @patch("web.middleware.user")
    def test_orgs_member(self, mock_user):
        Organization.objects.create(name="foo")
        self.req.user = self.user
        mock_user.check_org_membership.return_value = True
        self.assertEqual(self.check_orgs(self.req), True)

    @patch("web.middleware.user")
    def test_orgs_uses_cache(self, mock_user):
        Organization.objects.create(name="foo")
        self.req.user = self.user
        mock_user.check_org_membership.return_value = True
        self.assertEqual(self.check_orgs(self.req), True)
        assert mock_user.check_org_membership.call_count == 1

        # Second call should use cache.
        self.assertEqual(self.check_orgs(self.req), True)
        assert mock_user.check_org_membership.call_count == 1

    def test_login_not_required_anon(self):
        self.req = self.factory.get("/static/site.js")
        self.req.user = AnonymousUser()
        self.assertEqual(self.process_request(self.req), None)

    def test_login_not_required_user(self):
        self.req = self.factory.get("/static/site.js")
        self.req.user = self.user
        self.assertEqual(self.process_request(self.req), None)

    def test_login_required_user(self):
        self.req = self.factory.get("/services/")
        self.req.user = self.user
        self.assertEqual(self.process_request(self.req), None)

    def test_login_required_anon(self):
        self.req = self.factory.get("/services/")
        self.req.user = AnonymousUser()
        assert self.process_request(self.req)