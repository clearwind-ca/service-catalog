import json
import logging
import random
from unittest.mock import patch

from django.test import TestCase
from faker import Faker
from github import GithubException, UnknownObjectException

from catalog import errors
from services.models import Source

from .fetch import file_paths, get, get_file, login_as_user

logging.getLogger("faker").setLevel(logging.ERROR)
logging.getLogger("gh.fetch").setLevel(logging.ERROR)
fake = Faker("en_US")

from django.contrib.auth import get_user_model


class TestFetch(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="andy")
        self.user.oauth_connections.create(
            provider_key="github",
            provider_user_id=random.randint(1, 100),
            access_token=fake.password(),
            refresh_token=fake.password(),
        )
        self.source = Source.objects.create(name="andy/gh", host="G")
        return super().setUp()

    @patch("gh.fetch.Github")
    def test_login_as_user(self, gh_mock):
        """
        Test the login_as_user function, so that we can pass in
        a user object and get back a valid a Github object
        """
        gh = login_as_user(self.user)
        self.assertTrue(gh)
        assert gh_mock.called

    @patch("gh.fetch.Github")
    def test_get_file_errors(self, gh_mock):
        """
        Test the get_file function and catch the UnknownObjectException error
        and turn into a NoEntryFound error.
        """
        repo = gh_mock.get_repo("andy/gh")
        repo.get_contents.side_effect = UnknownObjectException(404, "Not Found", {})
        self.assertRaises(errors.NoEntryFound, get_file, repo)
        assert repo.get_contents.call_count == len(file_paths)

    @patch("gh.fetch.Github")
    def test_get_file_other_error(self, gh_mock):
        """
        Test the get_file function and catch the GithubException error.
        """
        repo = gh_mock.get_repo("andy/gh")
        repo.get_contents.side_effect = GithubException(404, "Not Found", {})
        self.assertRaises(GithubException, get_file, repo)
        assert repo.get_contents.call_count == 1

    @patch("gh.fetch.Github")
    def test_get_file_works(self, gh_mock):
        """
        Test that get_contents gets called if nothing goes wrong. This could
        probably be better since it doesn't test much.
        """
        repo = gh_mock.get_repo("andy/gh")
        get_file(repo)
        assert repo.get_contents.call_count

    @patch("gh.fetch.Github")
    @patch("gh.fetch.get_file")
    def test_get_data(self, get_file_mock, gh_mock):
        """
        Test that if nothing goes wrong, we get back some data from the server.
        """
        data = {"foo": "bar"}
        gh_mock.get_user.return_value = None
        get_file_mock.return_value = json.dumps(data)
        self.assertEquals(get(self.user, self.source), data)
