from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.test import TestCase
from faker import Faker
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from services.models import Organization
from web.groups import setup_group

fake = Faker("en_US")


class BaseTestCase(TestCase):
    """
    A base test case that setups users, tokens, orgs, and turns off org checking. Use for everything except checking those things.
    """

    def setUp(self):
        self.user = get_user_model().objects.create_user(username=fake.user_name())
        self.token = Token.objects.create(user=self.user)
        self.org = Organization.objects.create(name=fake.company())
        self.api_client = APIClient()
        settings.ENFORCE_ORG_MEMBERSHIP = False

        setup_group("members")
        setup_group("public")
        self.members = Group.objects.get(name="members")
        self.public = Group.objects.get(name="public")
        return super().setUp()

    def tearDown(self) -> None:
        cache.clear()
        settings.ENFORCE_ORG_MEMBERSHIP = True
        return super().tearDown()

    def login(self):
        self.client.force_login(self.user)

    def api_login(self):
        """Log in the user."""
        self.api_client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)

    def get_messages(self, response):
        """Get the messages from the response."""
        return list(messages.get_messages(response.wsgi_request))

    def get_message(self, response):
        """Get the first message from the response."""
        return self.get_messages(response)[0]

    def remove_api_token(self):
        """Remove the API token from the user."""
        self.token.delete()

    def add_to_members(self):
        """Add the user to the members group."""
        self.members.user_set.add(self.user)

    def add_to_public(self):
        """Add the user to the public group."""
        self.public.user_set.add(self.user)

    def remove_from_members(self):
        """Remove the user from the members group."""
        self.members.user_set.remove(self.user)

    def remove_from_public(self):
        """Remove the user from the public group."""
        self.public.user_set.remove(self.user)

    def login_required(self, res):
        self.assertEqual(res.status_code, 302)
        assert res.url.startswith(settings.LOGIN_URL), res.url