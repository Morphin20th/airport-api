from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

from airport.models import (
    Airplane,
    AirplaneType,
    Airport,
    Route,
    Crew,
    Flight
)


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ["id", "name"]


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ["id", "name", "airplane_type"]


class AirplaneListSerializer(AirplaneSerializer):
    airplane_type = SlugRelatedField(read_only=True, slug_field="name")


class AirplaneDetailSerializer(AirplaneSerializer):
    airplane_type = SlugRelatedField(queryset=AirplaneType.objects.all(), slug_field="name")

    class Meta:
        model = Airplane
        fields = ["id", "name", "rows", "seats_in_row", "airplane_type"]


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
    class Meta:
        model = Flight
        fields = [
            "id", "route", "airplane", "crewmates", "departure_time", "arrival_time"
        ]


class FlightListSerializer(FlightSerializer):
    airplane = serializers.SlugRelatedField(read_only=True, slug_field="name")
    route = serializers.StringRelatedField()
    crewmates = serializers.SerializerMethodField()

    def get_crewmates(self, obj):
        return [crew.full_name for crew in obj.crewmates.all()]


class FlightDetailSerializer(serializers.ModelSerializer):
    route = RouteDetailSerializer(read_only=True)
    airplane = AirplaneDetailSerializer(read_only=True)
    crewmates = CrewSerializer(read_only=True, many=True)

    class Meta:
        model = Flight
        fields = [
            "id", "route", "airplane", "crewmates", "departure_time", "arrival_time"
        ]
