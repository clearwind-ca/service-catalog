from django.urls import reverse

from catalog.helpers.tests import WithUser
from services.tests import create_service, create_source

from .models import Check, CheckResult


def create_health_check():
    source = create_source()
    service = create_service(source)
    health_check = Check.objects.create(name="Test Health Check")
    return {"source": source, "service": service, "health_check": health_check}


class TestAPI(WithUser):
    def setUp(self):
        super().setUp()
        created = create_health_check()
        self.source = created["source"]
        self.service = created["service"]
        self.health_check = created["health_check"]
        self.url = reverse("health:api-list")

    def test_add_result(self):
        data = {
            "service": self.service.pk,
            "result": "P",
            "message": "Test message",
            "status": "S",
        }
        self.api_login()
        response = self.api_client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(CheckResult.objects.count(), 1)
        self.assertEqual(CheckResult.objects.get().message, "Test message")
