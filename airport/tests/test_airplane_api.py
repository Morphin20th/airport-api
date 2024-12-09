import io
import os

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Airplane, AirplaneType
from airport.serializers import AirplaneListSerializer, AirplaneDetailSerializer

AIRPLANE_URL = reverse("airport:airplane-list")


def image_upload_url(airplane_id):
    return reverse("airport:airplane-upload-image", args=[airplane_id])


def detail_url(airplane_id):
    return reverse("airport:airplane-detail", args=[airplane_id])


def sample_airplane_type(**params):
    defaults = {
        "name": "Airliner"
    }
    defaults.update(params)
    return AirplaneType.objects.create(**defaults)


def sample_airplane(**params):
    defaults = {
        "name": "Boeing",
        "rows": 9,
        "seats_in_row": 70,
    }
    defaults.update(params)
    return Airplane.objects.create(**defaults)


class UnauthenticatedAirplaneApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AIRPLANE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirplaneApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.test", password="Test1234!", is_staff=False
        )
        self.client.force_authenticate(self.user)

    @classmethod
    def setUpTestData(cls):
        cls.airplane_type_1 = sample_airplane_type(name="test1")
        cls.airplane_type_2 = sample_airplane_type(name="test2")
        cls.airplane_1 = sample_airplane(name="test1", airplane_type=cls.airplane_type_1)
        cls.airplane_2 = sample_airplane(name="test2", airplane_type=cls.airplane_type_2)

    def test_airplane_list(self):
        sample_airplane(name="Airbus A220", airplane_type=self.airplane_type_1)
        res = self.client.get(AIRPLANE_URL)
        airplanes = Airplane.objects.all()
        serializer = AirplaneListSerializer(airplanes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)
        self.assertEqual(airplanes.count(), 3)

    def test_filter_airplanes_by_name(self):
        airplane = sample_airplane(name="Airbus A220", airplane_type=self.airplane_type_1)
        res = self.client.get(AIRPLANE_URL, {"name": f"{airplane}"})

        serializer_with_wrong_name = AirplaneListSerializer(self.airplane_1)
        serializer_with_correct_name = AirplaneListSerializer(airplane)

        self.assertIn(serializer_with_correct_name.data, res.data["results"])
        self.assertNotIn(serializer_with_wrong_name, res.data["results"])

    def test_filter_airplanes_by_airplane_type(self):
        airplane_type = sample_airplane_type()
        airplane_with_wrong_type = sample_airplane(airplane_type=airplane_type)
        res = self.client.get(AIRPLANE_URL, {"airplane-type": f"{self.airplane_type_1.id},{self.airplane_type_2.id}"})

        serializer_airplane_with_wrong_type_name = AirplaneListSerializer(airplane_with_wrong_type)
        serializer_airplane_with_type_1 = AirplaneListSerializer(self.airplane_1)
        serializer_airplane_with_type_2 = AirplaneListSerializer(self.airplane_2)

        self.assertNotIn(serializer_airplane_with_wrong_type_name, res.data["results"])
        self.assertIn(serializer_airplane_with_type_1.data, res.data["results"])
        self.assertIn(serializer_airplane_with_type_2.data, res.data["results"])

    def test_retrieve_airplane_detail(self):
        url = detail_url(self.airplane_1.id)

        res = self.client.get(url)

        serializer = AirplaneDetailSerializer(self.airplane_1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_airplane_forbidden(self):
        payload = {
            "name": "Boeing 747",
            "seats_in_row": 70,
            "rows": 9,
            "airplane_type": self.airplane_type_1
        }
        res = self.client.post(AIRPLANE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirplaneTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@admin.admin", password="Test1234!", is_staff=True
        )
        self.client.force_authenticate(self.user)
        self.airplane = sample_airplane(name="Boeing test", airplane_type=sample_airplane_type())

    @classmethod
    def setUpTestData(cls):
        cls.airplane_type_1 = sample_airplane_type(name="test1")
        cls.airplane_type_2 = sample_airplane_type(name="test2")
        cls.airplane_1 = sample_airplane(name="test1", airplane_type=cls.airplane_type_1)
        cls.airplane_2 = sample_airplane(name="test2", airplane_type=cls.airplane_type_2)

    def test_create_airplane(self):
        payload = {
            "name": "Boeing 747",
            "seats_in_row": 70,
            "rows": 9,
            "airplane_type": self.airplane_type_1
        }
        res = self.client.post(AIRPLANE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_delete_airplane_not_allowed(self):
        airplane = sample_airplane(airplane_type=self.airplane_type_1)
        url = detail_url(airplane.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_airplane_not_allowed(self):
        airplane = sample_airplane(airplane_type=self.airplane_type_1)
        payload = {"name": "Updated", "seats_in_row": 69}
        res = self.client.patch(f"{AIRPLANE_URL}{airplane.id}/", payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertNotEqual(airplane.name, payload["name"])
