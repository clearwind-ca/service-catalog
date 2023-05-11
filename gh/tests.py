import base64
import json
import random
from unittest.mock import patch

from django.shortcuts import reverse
from django.test import TestCase
from faker import Faker
from github import GithubException, UnknownObjectException

from catalog import errors
from services.tests import create_service, create_source
from health.tests import create_health_check, create_health_check_result
from events.models import Event
from services.models import Source

from .fetch import (
    file_paths,
    get,
    get_file,
    get_file_from_list,
    login_as_user,
    url_to_nwo,
)
from .send import dispatch
from .webhooks import handle_deployment, handle_release

fake = Faker("en_US")

from django.contrib.auth import get_user_model


class WithGitHubUser(TestCase):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user(username=fake.name())
        self.user.oauth_connections.create(
            provider_key="github",
            provider_user_id=random.randint(1, 100),
            access_token=fake.password(),
            refresh_token=fake.password(),
        )


class TestUser(WithGitHubUser):
    @patch("gh.user.Github")
    def test_login_as_user(self, gh_mock):
        """
        Test the login_as_user function, so that we can pass in
        a user object and get back a valid a Github object
        """
        gh = login_as_user(self.user)
        self.assertTrue(gh)
        assert gh_mock.called


class TestFetch(WithGitHubUser):
    def setUp(self):
        super().setUp()
        self.source = Source.objects.create(url="https://gh.com/andy/gh")
        self.simple_data = {"priority": 1, "name": "test", "type": "widget"}

    @patch("gh.user.Github")
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

    @patch("gh.user.Github")
    @patch("gh.fetch.get_contents")
    def test_get_file_other_error(self, get_contents_mock, gh_mock):
        """
        Test the get_file function and catch the GithubException error.
        """
        repo = gh_mock.get_repo("andy/gh")
        get_contents_mock.side_effect = GithubException(404, "Not Found", {})
        self.assertRaises(GithubException, get_file, repo, "catalog.json")
        assert get_contents_mock.call_count == 1

    @patch("gh.user.Github")
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

    @patch("gh.fetch.login_as_app")
    @patch("gh.fetch.login_as_installation")
    @patch("gh.fetch.get_contents")
    def test_get_data(self, get_contents_mock, as_installation_mock, as_app_mock):
        """
        Test that if nothing goes wrong, we get back some data from the server.
        """
        data = {"contents": self.simple_data, "path": "catalog.json"}
        get_contents_mock.return_value = self.simple_data
        result = get(self.source)
        self.assertEquals(len(result), 1)
        self.assertEquals(result[0], data)

    @patch("gh.fetch.login_as_app")
    @patch("gh.fetch.login_as_installation")
    @patch("gh.fetch.get_contents")
    def test_get_data_more_files(self, get_contents_mock, as_installation_mock, as_app_mock):
        """
        Test that it looks up file contents for all the files.
        """
        data = {
            "priority": 1,
            "name": "test",
            "type": "widget",
            "files": ["catalog2.json"],
        }
        get_contents_mock.return_value = data
        result = get(self.source)
        self.assertEquals(len(result), 2)
        self.assertEquals(result[1], {"contents": data, "path": "catalog2.json"})


def unpack_payload(payload):
    return json.loads(base64.b64decode(payload).decode("utf-8"))


class TestSend(WithGitHubUser):
    @patch("gh.send.get_repo_installation")
    def test_dispatch_created(self, login_mock):
        """
        Sends a dispatch event to the repository
        """
        objects = create_health_check()
        result = create_health_check_result(objects["health_check"], objects["service"])
        with self.settings(GITHUB_CHECK_REPOSITORY="https://github.com/foo/bar"):
            dispatch(result)
        args = login_mock.return_value.create_repository_dispatch.call_args
        self.assertEqual(args[1]["event_type"], "check")

        payload = unpack_payload(args[1]["client_payload"]["data"])
        assert isinstance(payload, dict)
        assert "server" in payload.keys()

    @patch("gh.fetch.login_as_app")
    def test_dispatch_failed(self, gh_mock):
        """
        Test error when the repo fails on the dispatch call
        """
        objects = create_health_check()
        result = create_health_check_result(objects["health_check"], objects["service"])
        gh_mock.return_value.get_repo_installation.side_effect = UnknownObjectException(
            "", "data", {}
        )
        with self.settings(GITHUB_CHECK_REPOSITORY="https://github.com/foo/bar"):
            self.assertRaises(errors.NoRepository, dispatch, result)


class Test(TestCase):
    def test_nwo(self):
        """
        Test that the nwo function returns the right values
        """
        for x, y in [
            ["https://github.com/andymckay/blog", ("andymckay", "blog")],
            ["foo/bar", ("foo", "bar")],
            ["/foo/bar", ("foo", "bar")],
            ["/foo/bar/", ("foo", "bar")],
        ]:
            self.assertEqual(url_to_nwo(x), y)

    def test_nwo_errors(self):
        """
        Test that NWO errors when it should.
        """
        for x in ["foo/bar/baz", "/foo", "foo", "http://github.com"]:
            self.assertRaises(ValueError, url_to_nwo, x)


class TestWebhook(WithGitHubUser):
    def setUp(self):
        super().setUp()
        self.url = reverse("github:webhooks")
        self.source = create_source()
        self.service = create_service(self.source)

    def test_deployment_no_mocks(self):
        self.assertEqual(self.client.post(self.url).status_code, 400)

    def get_deployment_payload(self):
        return {
            "deployment": {
                "description": "",
                "environment": "production",
                "url": fake.url(),
                "id": fake.random_int(),
                "statuses_url": fake.url()
            },
            "repository": {
                "html_url": self.source.url,
            },
        }

    @patch("gh.webhooks.requests.get")
    def test_handle_deployment(self, mock_get):
        mock_get.return_value.json.return_value = [{ "state": "success" }]
        handle_deployment(self.get_deployment_payload())
        
        event = Event.objects.get()
        self.assertEqual(event.type, "deployment")
        self.assertEqual(event.status, "success")

    def test_handle_deployment_inactive_service(self):
        self.service.active = False
        self.service.save()

        handle_deployment(self.get_deployment_payload())
        self.assertFalse(Event.objects.exists())    
    
    def test_handle_no_event_service(self):
        self.service.events = []
        self.service.save()

        handle_deployment(self.get_deployment_payload())
        self.assertFalse(Event.objects.exists())    
    
    @patch("gh.webhooks.requests.get")
    def test_handle_multiple_services(self, mock_get):
        mock_get.return_value.json.return_value = [{ "state": "success" }]
        create_service(self.source)

        handle_deployment(self.get_deployment_payload())
        self.assertEqual(Event.objects.count(), 2)