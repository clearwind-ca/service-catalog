import json
import logging
import random
from unittest.mock import patch

from django.test import TestCase
from faker import Faker
from github import GithubException, UnknownObjectException

from catalog import errors
from services.models import Source

from .fetch import file_paths, get, get_file, get_file_from_list, login_as_user

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
        self.source = Source.objects.create(url="https://gh.com/andy/gh")
        self.simple_data = {"priority": 1, "name": "test", "type": "widget"}
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
    @patch("gh.fetch.get_contents")
    def test_get_file_errors(self, get_contents_mock, gh_mock):
        """
        Test the get_file function and catch the UnknownObjectException error
        and turn into a NoEntryFound error.
        """
        repo = gh_mock.get_repo("andy/gh")
        get_contents_mock.side_effect = UnknownObjectException(404, "Not Found", {})
        self.assertRaises(errors.NoEntryFound, get_file_from_list, repo, file_paths)
        assert get_contents_mock.call_count == len(file_paths)

    @patch("gh.fetch.Github")
    @patch("gh.fetch.get_contents")
    def test_get_file_other_error(self, get_contents_mock, gh_mock):
        """
        Test the get_file function and catch the GithubException error.
        """
        repo = gh_mock.get_repo("andy/gh")
        get_contents_mock.side_effect = GithubException(404, "Not Found", {})
        self.assertRaises(GithubException, get_file, repo, "catalog.json")
        assert get_contents_mock.call_count == 1

    @patch("gh.fetch.Github")
    @patch("gh.fetch.get_contents")
    def test_get_file_works(self, get_contents_mock, gh_mock):
        """
        Test that get_contents gets called if nothing goes wrong. This could
        probably be better since it doesn't test much.
        """
        repo = gh_mock.get_repo("andy/gh")
        get_contents_mock.return_value = {
            "contents": self.simple_data,
            "path": "catalog.json",
        }
        get_file(repo, "catalog.json")
        assert get_contents_mock.call_count

    @patch("gh.fetch.Github")
    @patch("gh.fetch.get_contents")
    def test_get_data(self, get_contents_mock, gh_mock):
        """
        Test that if nothing goes wrong, we get back some data from the server.
        """
        data = {"contents": self.simple_data, "path": "catalog.json"}
        gh_mock.get_user.return_value = None
        get_contents_mock.return_value = self.simple_data
        result = get(self.user, self.source)
        self.assertEquals(len(result), 1)
        self.assertEquals(result[0], data)

    @patch("gh.fetch.Github")
    @patch("gh.fetch.get_contents")
    def test_get_data_more_files(self, get_contents_mock, gh_mock):
        """
        Test that it looks up file contents for all the files.
        """
        data = {
            "priority": 1,
            "name": "test",
            "type": "widget",
            "files": ["catalog2.json"],
        }
        gh_mock.get_user.return_value = None
        get_contents_mock.return_value = data
        result = get(self.user, self.source)
        self.assertEquals(len(result), 2)
        self.assertEquals(result[1], {"contents": data, "path": "catalog2.json"})
