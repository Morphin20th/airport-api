from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from airport.models import Order, Ticket
from airport.tests.test_airplane_api import sample_airplane
from airport.tests.test_flight_api import sample_flight
from airport.tests.test_route_api import sample_source, sample_destination, sample_route

ORDER_URL = reverse("airport:order-list")


class UnauthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ORDER_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = get_user_model().objects.create_user(
            email="admin@admin.admin", password="Test1234!", is_staff=True
        )
        self.user = get_user_model().objects.create_user(
            email="test@test.test", password="Test1234!", is_staff=False
        )
        self.client.force_authenticate(self.user)

        self.source_1 = sample_source(name="test_source_1", closest_big_city="Test")
        self.destination_1 = sample_destination(name="test_destination_1", closest_big_city="Test")
        self.route_1 = sample_route(source=self.source_1, destination=self.destination_1)
        self.airplane_1 = sample_airplane(name="Test_1")
        self.flight_1 = sample_flight(
            route=self.route_1, airplane=self.airplane_1,
            departure_time="2024-12-12 12:00:00", arrival_time="2024-12-12 13:00:00"
        )
        self.order = Order.objects.create(user=self.user)
        self.ticket = Ticket.objects.create(row=1, seat=1, flight=self.flight_1, order=self.order)

    def test_create_order_with_valid_data(self):
        data = {
            "tickets": [
                {"row": 2, "seat": 2, "flight": self.flight_1.id}
            ]
        }
        res = self.client.post(ORDER_URL, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 2)

    def test_create_order_without_tickets(self):
        data = {}
        res = self.client.post(ORDER_URL, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_with_invalid_ticket(self):
        data = {
            "tickets": [
                {"row": 11, "seat": 71, "flight": self.flight_1.id}
            ]
        }
        res = self.client.post(ORDER_URL, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_orders(self):
        res = self.client.get(ORDER_URL)
        orders = Order.objects.all()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(orders.count(), 1)

    def test_list_orders_not_owned_by_user(self):
        self.client.force_authenticate(self.admin_user)
        res = self.client.get(ORDER_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 0)
