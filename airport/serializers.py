from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.relations import SlugRelatedField
from rest_framework.validators import UniqueTogetherValidator

from airport.models import (
    Airplane,
    AirplaneType,
    Airport,
    Route,
    Crew,
    Flight,
    Ticket,
    Order
)


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ["id", "name"]


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ["id", "image"]


class AirplaneListSerializer(AirplaneSerializer):
    airplane_type = SlugRelatedField(read_only=True, slug_field="name")

    class Meta:
        model = Airplane
        fields = ["id", "name", "airplane_type", "image"]


class AirplaneDetailSerializer(AirplaneSerializer):
    airplane_type = SlugRelatedField(
        queryset=AirplaneType.objects.all(), slug_field="name"
    )

    class Meta:
        model = Airplane
        fields = [
            "id", "name", "rows", "seats_in_row", "airplane_type", "image"
        ]


class AirplaneImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ("id", "image",)


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ["id", "name", "closest_big_city"]


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ["id", "source", "destination", "distance"]


class RouteListSerializer(RouteSerializer):
    source = SlugRelatedField(read_only=True, slug_field="name")
    destination = SlugRelatedField(read_only=True, slug_field="name")


class RouteDetailSerializer(RouteSerializer):
    source = SlugRelatedField(
        queryset=Airport.objects.all(), slug_field="name"
    )
    destination = SlugRelatedField(
        queryset=Airport.objects.all(), slug_field="name"
    )


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ["id", "first_name", "last_name", "full_name"]


class FlightSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(FlightSerializer, self).validate(attrs=attrs)
        Flight.validate_time(
            attrs["departure_time"],
            attrs["arrival_time"],
            ValidationError
        )
        return data

    departure_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    arrival_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Flight
        fields = [
            "id",
            "route",
            "airplane",
            "crewmates",
            "departure_time",
            "arrival_time",
        ]
        validators = [
            UniqueTogetherValidator(
                queryset=Flight.objects.all(),
                fields=["route", "airplane", "departure_time"],
                message="A flight with this route, "
                        "airplane, and departure time already exists.",
            )
        ]


class FlightListSerializer(FlightSerializer):
    airplane = serializers.SlugRelatedField(read_only=True, slug_field="name")
    route = serializers.StringRelatedField()
    crewmates = serializers.SerializerMethodField()
    tickets_available = serializers.SerializerMethodField()

    def get_crewmates(self, obj):
        return [crew.full_name for crew in obj.crewmates.all()]

    def get_tickets_available(self, obj):
        total_seats = obj.airplane.rows * obj.airplane.seats_in_row
        occupied_seats = obj.tickets.count()
        return total_seats - occupied_seats

    class Meta:
        model = Flight
        fields = [
            "id",
            "route",
            "airplane",
            "crewmates",
            "departure_time",
            "arrival_time",
            "tickets_available"
        ]


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            attrs["flight"].airplane,
            ValidationError,
        )
        return data

    class Meta:
        model = Ticket
        fields = ["id", "row", "seat", "flight"]
        ordering = ("id", "row", "seat", "flight")
        validators = [
            UniqueTogetherValidator(
                queryset=Ticket.objects.all(),
                fields=["row", "seat", "flight"],
                message="A ticket with this seat and row "
                        "already exists for the given flight."
            )
        ]


class TicketListSerializer(TicketSerializer):
    flight = FlightListSerializer(read_only=True)


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class FlightDetailSerializer(FlightSerializer):
    route = RouteDetailSerializer(read_only=True)
    airplane = AirplaneDetailSerializer(read_only=True)
    crewmates = CrewSerializer(read_only=True, many=True)
    taken_places = TicketSeatsSerializer(
        source="tickets", many=True, read_only=True
    )

    class Meta:
        model = Flight
        fields = [
            "id",
            "route",
            "airplane",
            "crewmates",
            "departure_time",
            "arrival_time",
            "taken_places"
        ]


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ["id", "tickets", "created_at"]

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
