from datetime import timedelta
from unittest.mock import Mock, patch
from urllib.parse import urlencode

from django.urls import reverse
from django.utils import timezone
from faker import Faker

from catalog.helpers.tests import WithUser
from services.tests import create_service, create_source

from . import models
from .models import Event
from .tasks import get_all_active_deployments, get_deployments

fake = Faker()


class WithEvents(WithUser):
    def setUp(self):
        super().setUp()
        self.source = create_source()
        self.services = []
        for _ in range(3):
            self.services.append(create_service(self.source))
        self.services_pks = [s.pk for s in self.services]

    def get_event_data(self):
        return {
            "name": fake.name(),
            "description": fake.text(),
            "type": fake.name(),
            "start": fake.date_time(),
            "end": fake.date_time(),
            "active": fake.boolean(),
            "url": fake.url(),
            "source": fake.text(),
            "external_id": fake.text(),
            "customers": fake.boolean(),
        }

    def create_event(self):
        event = models.Event.objects.create(**self.get_event_data())
        for service in fake.random_elements(self.services_pks, length=2, unique=True):
            event.services.add(service)
        return event

    def create_event_at_time(self, seconds, active=True):
        event = self.create_event()
        event.start = timezone.now() + timedelta(seconds=seconds)
        event.active = active
        event.save()
        return event

    def event_in_results(self, res, event):
        return event.pk in [e.pk for e in res.context["events"].object_list]

    def get_list(self, params=None):
        url = reverse("events:events-list")
        # According to docs we should be able to pass params to the client.get
        # ...but that didn't seem to work.
        if params:
            url = f"{url}?{urlencode(params)}"
        self.client.force_login(user=self.user)
        return self.client.get(url)


class TestEventList(WithEvents):
    def test_create_event_login_required(self):
        """Test that we need to post to create."""
        self.url = reverse("events:events-add")
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Event.objects.count(), 0)

    def test_create_event(self):
        """Test that we can post an event."""
        url = reverse("events:events-add")
        self.client.force_login(user=self.user)
        res = self.client.post(url, data=self.get_event_data())
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Event.objects.count(), 1)

    def test_update_event(self):
        """Test that we can update an event."""
        event = self.create_event()
        url = reverse("events:events-update", kwargs={"pk": event.pk})
        self.client.force_login(user=self.user)
        res = self.client.post(url, data=self.get_event_data())
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Event.objects.count(), 1)

    def test_delete_event(self):
        """Test that we can delete an event"""
        event = self.create_event()
        url = reverse("events:events-delete", kwargs={"pk": event.pk})
        self.client.force_login(user=self.user)
        res = self.client.post(url)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Event.objects.count(), 0)

    def test_get_api(self):
        """Test that we can get an object via the API"""
        event = self.create_event()
        url = reverse("events:api-events-detail", kwargs={"pk": event.pk})
        self.api_login()
        res = self.api_client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("name"), event.name)

    def test_list_api(self):
        """Test that we can list via the API"""
        event = self.create_event()
        url = reverse("events:api-events-list")
        self.api_login()
        res = self.api_client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["results"][0].get("name"), event.name, res.json())

    def test_create_api(self):
        """Test that we can create via the API"""
        url = reverse("events:api-events-list")
        self.api_login()
        res = self.api_client.post(url, data=self.get_event_data())
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Event.objects.count(), 1)

    def test_update_api(self):
        """Test that we can update via the API"""
        event = self.create_event()
        url = reverse("events:api-events-detail", kwargs={"pk": event.pk})
        self.api_login()
        res = self.api_client.patch(url, data={"name": "new name"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Event.objects.get(pk=event.pk).name, "new name")

    def test_delete_api(self):
        """Test that we can delete via the API"""
        event = self.create_event()
        url = reverse("events:api-events-detail", kwargs={"pk": event.pk})
        self.api_login()
        res = self.api_client.delete(url)
        self.assertEqual(res.status_code, 204)

    def test_list_filters_recent(self):
        event = self.create_event_at_time(seconds=-600, active=True)
        res = self.get_list()
        self.assertEqual(res.context["ordering"], "-start")
        self.assertEqual(res.context["filters"]["when"], "recent")
        self.assertTrue(self.event_in_results(res, event))

    def test_list_filters_out_active(self):
        event = self.create_event_at_time(seconds=-600, active=False)
        res = self.get_list()
        self.assertEqual(res.context["ordering"], "-start")
        self.assertEqual(res.context["filters"]["when"], "recent")
        self.assertFalse(self.event_in_results(res, event))

    def test_list_filters_future(self):
        past = self.create_event_at_time(seconds=-600, active=True)
        future = self.create_event_at_time(seconds=600, active=True)
        res = self.get_list(params={"when": "future"})
        self.assertEqual(res.context["ordering"], "start")
        self.assertEqual(res.context["filters"]["when"], "future")
        self.assertFalse(self.event_in_results(res, past))
        self.assertTrue(self.event_in_results(res, future))

    def test_list_filters_past(self):
        past = self.create_event_at_time(seconds=-600, active=True)
        future = self.create_event_at_time(seconds=600, active=True)
        res = self.get_list(params={"when": "past"})
        self.assertEqual(res.context["ordering"], "-start")
        self.assertEqual(res.context["filters"]["when"], "past")
        self.assertFalse(self.event_in_results(res, future))
        self.assertTrue(self.event_in_results(res, past))


class TestDeployments(WithEvents):
    def setUp(self):
        super().setUp()
        self.username = self.user.username
        self.service = self.services[0]

    @patch("events.tasks.fetch")
    def test_get_only_active(self, mock_fetch):
        """Test that we only get deployments for active services"""
        self.service.active = False
        self.service.save()

        with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
            get_all_active_deployments(self.username)
        self.assertEqual(mock_fetch.get_deployments.call_count, 2)

    @patch("events.tasks.fetch")
    def test_get_only_deployment(self, mock_fetch):
        """Test that we only get services that have deployments"""
        self.service.active = False
        self.service.save()

        self.services[1].events = []
        self.services[1].save()

        with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
            get_all_active_deployments(self.username)
        self.assertEqual(mock_fetch.get_deployments.call_count, 1)

    def setupMocks(self):
        status = Mock()
        status.created_at = timezone.now()
        status.state = fake.name()

        statuses = Mock()

        deployment = Mock()
        deployment.id = fake.random_int()
        deployment.get_statuses.return_value = [statuses]
        deployment.created_at = fake.date_time()
        deployment.url = fake.url()
        deployment.get_status.return_value = status
        return deployment

    @patch("events.tasks.fetch")
    def test_get_deployments(self, mock_fetch):
        """Test that we create a deployment"""
        deployment = self.setupMocks()
        mock_fetch.get_deployments.return_value = [deployment]

        with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
            get_deployments.delay(self.username, self.service.slug)

        self.assertEquals(Event.objects.all().count(), 1)
        event = Event.objects.get()
        self.assertEqual([s.slug for s in event.services.all()], [self.service.slug])

    @patch("events.tasks.fetch")
    def test_ignore_deployments(self, mock_fetch):
        """Test that we ignore deployments we've seen"""
        deployment = self.setupMocks()
        mock_fetch.get_deployments.return_value = [deployment]
        event = self.create_event()
        event.external_id = deployment.id
        event.save()

        self.assertEquals(Event.objects.all().count(), 1)

        with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
            get_deployments.delay(self.username, self.service.slug)

        self.assertEquals(Event.objects.all().count(), 1)
