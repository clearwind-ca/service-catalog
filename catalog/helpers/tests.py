import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.test import TestCase
from faker import Faker
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

logging.getLogger("faker").setLevel(logging.ERROR)
fake = Faker("en_US")


class WithUser(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username=fake.user_name())
        self.token = Token.objects.create(user=self.user)
        self.api_client = APIClient()
        return super().setUp()

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
