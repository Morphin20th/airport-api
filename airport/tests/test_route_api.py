from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from airport.models import Airport, Route
from airport.serializers import RouteListSerializer, RouteDetailSerializer

ROUTE_URL = reverse("airport:route-list")


def detail_url(route_id):
    return reverse("airport:route-detail", args=[route_id])


def sample_source(**params):
    defaults = {
        "name": "Zhuliany",
        "closest_big_city": "Kyiv"
    }
    defaults.update(params)
    return Airport.objects.create(**defaults)


def sample_destination(**params):
    defaults = {
        "name": "Borispol",
        "closest_big_city": "Kyiv"
    }
    defaults.update(params)
    return Airport.objects.create(**defaults)


def sample_route(**params):
    defaults = {"distance": 70}
    defaults.update(params)
    return Route.objects.create(**defaults)


class UnauthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ROUTE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.test", password="Test1234!", is_staff=False
        )
        self.client.force_authenticate(self.user)

    @classmethod
    def setUpTestData(cls):
        cls.source_1 = sample_source()
        cls.source_2 = sample_source(name="test_source", closest_big_city="Test")
        cls.destination_1 = sample_destination()
        cls.destination_2 = sample_destination(name="test_destination", closest_big_city="Test")
        cls.route_1 = sample_route(source=cls.source_1, destination=cls.destination_1)
        cls.route_2 = sample_route(source=cls.source_2, destination=cls.destination_2)

    def test_route_list(self):
        res = self.client.get(ROUTE_URL)
        routes = Route.objects.all()
        serializer = RouteListSerializer(routes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)
        self.assertEqual(routes.count(), 2)

    def test_filter_routes_by_source(self):
        res = self.client.get(
            ROUTE_URL, {"source": f"{self.source_1.id}"}
        )

        serializer_route_with_wrong_source_name = RouteListSerializer(self.route_2)
        serializer_route_with_correct_source = RouteListSerializer(self.route_1)

        self.assertNotIn(serializer_route_with_wrong_source_name.data, res.data["results"])
        self.assertIn(serializer_route_with_correct_source.data, res.data["results"])

    def test_filter_routes_by_destination(self):
        res = self.client.get(
            ROUTE_URL, {"source": f"{self.source_1.id}"}
        )

        serializer_route_with_wrong_destination_name = RouteListSerializer(self.route_2)
        serializer_route_with_destination = RouteListSerializer(self.route_1)

        self.assertNotIn(serializer_route_with_wrong_destination_name.data, res.data["results"])
        self.assertIn(serializer_route_with_destination.data, res.data["results"])

    def test_retrieve_route_detail(self):
        url = detail_url(self.route_1.id)

        res = self.client.get(url)

        serializer = RouteDetailSerializer(self.route_1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_route_forbidden(self):
        payload = {
            "source": self.source_1,
            "destination": self.destination_1,
            "distance": 70,
        }
        res = self.client.post(ROUTE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@admin.admin", password="Test1234!", is_staff=True
        )
        self.client.force_authenticate(self.user)

    @classmethod
    def setUpTestData(cls):
        cls.source_1 = sample_source()
        cls.source_2 = sample_source(name="test_source", closest_big_city="Test")
        cls.destination_1 = sample_destination()
        cls.destination_2 = sample_destination(name="test_destination", closest_big_city="Test")
        cls.route_1 = sample_route(source=cls.source_1, destination=cls.destination_1)
        cls.route_2 = sample_route(source=cls.source_2, destination=cls.destination_2)

    def test_create_route(self):
        payload = {
            "source": self.source_1.id,
            "destination": self.destination_1.id,
            "distance": 30,
        }
        res = self.client.post(ROUTE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_delete_route_not_allowed(self):
        url = detail_url(self.route_1.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_route_not_allowed(self):
        payload = {"source": self.source_2.id, "destination": self.destination_2.id, "distance": 30}
        res = self.client.patch(f"{ROUTE_URL}{self.route_1.id}/", payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertNotEqual(self.route_1.source, payload["source"])
        self.assertNotEqual(self.route_1.destination, payload["destination"])
        self.assertNotEqual(self.route_1.distance, payload["distance"])
