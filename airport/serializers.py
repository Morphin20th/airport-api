from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

from airport.models import Airplane, AirplaneType


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
