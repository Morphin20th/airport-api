from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from airport.models import AirplaneType
from airport.serializers import AirplaneTypeSerializer

AIRPLANE_TYPE_URL = reverse("airport:airplanetype-list")


def detail_url(airplane_type_id):
    return reverse("airport:airplanetype-detail", args=[airplane_type_id])


def sample_airplane_type(**params):
    defaults = {
        "name": "Airliner"
    }
    defaults.update(params)
    return AirplaneType.objects.create(**defaults)


class UnauthenticatedAirplaneTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AIRPLANE_TYPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirplaneTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.test", password="Test1234!", is_staff=False
        )
        self.client.force_authenticate(self.user)
        self.airplane_type_1 = sample_airplane_type()

    def test_airplane_type_list(self):
        sample_airplane_type(name="test")
        res = self.client.get(AIRPLANE_TYPE_URL)
        airplane_types = AirplaneType.objects.all()
        serializer = AirplaneTypeSerializer(airplane_types, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)
        self.assertEqual(airplane_types.count(), 2)

    def test_retrieve_airplane_type_detail_not_exists(self):
        with self.assertRaises(NoReverseMatch):
            reverse("airport:airplanetype-detail", args=[self.airplane_type_1.id])

    def test_create_airplane_type_forbidden(self):
        payload = {
            "name": "test_2",
        }
        res = self.client.post(AIRPLANE_TYPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirplaneTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@admin.admin", password="Test1234!", is_staff=True
        )
        self.client.force_authenticate(self.user)
        self.airplane_type_1 = sample_airplane_type()

    def test_airplane_type_delete_not_allowed(self):
        url = f"/api/airport/airplane-type/{self.airplane_type_1.id}/"

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_airplane_type_update_not_allowed(self):
        url = f"/api/airport/airplane-type/{self.airplane_type_1.id}/"
        payload = {"name": "Updated Airplane Type"}

        res_put = self.client.put(url, payload)
        self.assertEqual(res_put.status_code, status.HTTP_404_NOT_FOUND)

        res_patch = self.client.patch(url, payload)
        self.assertEqual(res_patch.status_code, status.HTTP_404_NOT_FOUND)