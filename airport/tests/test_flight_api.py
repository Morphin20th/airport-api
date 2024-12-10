from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from .test_airplane_api import sample_airplane
from .test_route_api import sample_route, sample_destination, sample_source
from ..models import Flight, Crew
from ..serializers import FlightListSerializer, FlightDetailSerializer

FLIGHT_URL = reverse("airport:flight-list")


def detail_url(flight_id):
    return reverse("airport:flight-detail", args=[flight_id])


def sample_flight(**params):
    defaults = {
        "departure_time": "2024-11-11 11:00:00",
        "arrival_time": "2024-11-11 12:00:00"
    }
    defaults.update(params)
    return Flight.objects.create(**defaults)


class UnauthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(FLIGHT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.test", password="Test1234!", is_staff=False
        )
        self.client.force_authenticate(self.user)

    @classmethod
    def setUpTestData(cls):
        cls.source_1 = sample_source(name="test_source_1", closest_big_city="Test")
        cls.source_2 = sample_source(name="test_source_2", closest_big_city="Test")
        cls.destination_1 = sample_destination(name="test_destination_1", closest_big_city="Test")
        cls.destination_2 = sample_destination(name="test_destination_2", closest_big_city="Test")
        cls.route_1 = sample_route(source=cls.source_1, destination=cls.destination_1)
        cls.route_2 = sample_route(source=cls.source_2, destination=cls.destination_2)
        cls.crewmate_1 = Crew.objects.create(first_name="Test1", last_name="Test1")
        cls.crewmate_2 = Crew.objects.create(first_name="Test1", last_name="Test1")
        cls.airplane_1 = sample_airplane(name="Test_1")
        cls.airplane_2 = sample_airplane(name="Test_2")
        cls.flight_1 = sample_flight(
            route=cls.route_1, airplane=cls.airplane_1,
            departure_time="2024-12-12 12:00:00", arrival_time="2024-12-12 13:00:00"
        )
        cls.flight_2 = sample_flight(
            route=cls.route_2,
            airplane=cls.airplane_2,
        )
        cls.flight_1.crewmates.add(cls.crewmate_1)
        cls.flight_2.crewmates.add(cls.crewmate_2)

    def test_flight_list(self):
        res = self.client.get(FLIGHT_URL)
        flights = Flight.objects.all()
        serializer = FlightListSerializer(flights, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)
        self.assertEqual(flights.count(), 2)

    def test_filter_flights_by_route(self):
        res = self.client.get(
            FLIGHT_URL, {"routes": f"{self.route_1.id}"}
        )

        serializer_flight_with_wrong_route = FlightListSerializer(self.flight_2)
        serializer_flight_with_correct_route = FlightListSerializer(self.flight_1)

        self.assertNotIn(serializer_flight_with_wrong_route.data, res.data["results"])
        self.assertIn(serializer_flight_with_correct_route.data, res.data["results"])

    def test_filter_flights_by_airplane(self):
        res = self.client.get(
            FLIGHT_URL, {"airplanes": f"{self.airplane_1.id}"}
        )

        serializer_flight_with_wrong_airplane = FlightListSerializer(self.flight_2)
        serializer_flight_with_correct_airplane = FlightListSerializer(self.flight_1)

        self.assertNotIn(serializer_flight_with_wrong_airplane.data, res.data["results"])
        self.assertIn(serializer_flight_with_correct_airplane.data, res.data["results"])

    def test_filter_flights_by_date(self):
        valid_date = "2024-12-12"
        res = self.client.get(FLIGHT_URL, {"departure-date": f"{valid_date}"})

        serializer_with_wrong_date = FlightListSerializer(self.flight_2)
        serializer_with_correct_date = FlightListSerializer(self.flight_1)

        self.assertIn(serializer_with_correct_date.data, res.data["results"])
        self.assertNotIn(serializer_with_wrong_date, res.data["results"])

    def test_validate_time_raises_error_for_invalid_time(self):
        invalid_departure_time = "2024-12-12 15:00:00"
        invalid_arrival_time = "2024-12-12 14:00:00"

        flight = Flight(
            route=self.route_1,
            airplane=self.airplane_1,
            departure_time=invalid_departure_time,
            arrival_time=invalid_arrival_time,
        )

        with self.assertRaises(ValidationError) as error:
            flight.clean()

        self.assertIn(
            "Departure time", str(error.exception),
            "Expected ValidationError for invalid flight times"
        )

    def test_retrieve_flight_detail(self):
        url = detail_url(self.flight_1.id)

        res = self.client.get(url)

        serializer = FlightDetailSerializer(self.flight_1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


class AdminFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@admin.admin", password="Test1234!", is_staff=True
        )
        self.client.force_authenticate(self.user)
        self.source_1 = sample_source(name="test_source_1", closest_big_city="Test")
        self.destination_1 = sample_destination(name="test_destination_1", closest_big_city="Test")
        self.route_1 = sample_route(source=self.source_1, destination=self.destination_1)
        self.airplane_1 = sample_airplane(name="Test_1")

    def test_create_flight(self):
        payload = {
            "route": self.route_1.id,
            "airplane": self.airplane_1.id,
            "departure_time": "2024-12-12 12:00:00",
            "arrival_time": "2024-12-12 13:00:00"
        }
        res = self.client.post(FLIGHT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_delete_airplane(self):
        flight = sample_flight(route=self.route_1, airplane=self.airplane_1)
        url = detail_url(flight.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)