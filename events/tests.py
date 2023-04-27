import os
from unittest.mock import patch

from auditlog.models import LogEntry
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models.deletion import ProtectedError
from django.forms.models import model_to_dict
from django.test import TestCase
from django.urls import reverse
from faker import Faker

from catalog.errors import FetchError
from catalog.helpers.tests import WithUser
from web.shortcuts import get_object_or_None

from .models import Event
from . import forms, models
from services.tests import create_service, create_source

fake = Faker()


class TestEvents(WithUser):
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
            "type": fake.random_element(models.EVENT_TYPES)[0],
            "start": fake.date_time(),
            "end": fake.date_time(),
            "active": fake.boolean(),
            "external_url": fake.url(),
            "external_source": fake.text(),
            "external_id": fake.text(),
            "customers": fake.boolean(),
            "services": fake.random_elements(self.services_pks, length=2, unique=True),
        }
    
    def create_event():
        return models.Event.objects.create(**self.get_event_data())

    def test_create_event_login_required(self):
        """Test that we need to post to create."""
        self.url = reverse("events:events-add")
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Event.objects.count(), 0)

    def test_create_event(self):
        """Test that we can post an event."""
        self.url = reverse("events:events-add")
        self.client.force_login(user=self.user)
        res = self.client.post(self.url, data=self.get_event_data())
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Event.objects.count(), 1)