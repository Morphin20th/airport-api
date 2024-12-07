from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from airport.models import Airplane, AirplaneType, Airport, Route, Crew, Flight, Order
from airport.serializers import (
    AirplaneSerializer,
    AirplaneTypeSerializer,
    AirplaneListSerializer,
    AirplaneDetailSerializer,
    AirplaneImageSerializer,
    AirportSerializer,
    RouteSerializer,
    RouteListSerializer,
    RouteDetailSerializer,
    CrewSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    FlightSerializer,
    OrderSerializer,
    OrderListSerializer,
)


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


def _params_to_ints(qs):
    """Converts a list of string IDs to a list of integers"""
    return [int(str_id) for str_id in qs.split(",")]


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        if self.action == "retrieve":
            return AirplaneDetailSerializer
        if self.action in ("create", "update", "partial_update"):
            return AirplaneDetailSerializer
        if self.action == "upload-image":
            return AirplaneImageSerializer
        return AirplaneSerializer

    def get_queryset(self):
        """Retrieve the airplanes with filters"""
        name = self.request.query_params.get("name")
        airplane_type = self.request.query_params.get("airplane-type")

        queryset = self.queryset

        if name:
            queryset = queryset.filter(name__icontains=name)

        if airplane_type:
            airplane_type_ids = _params_to_ints(airplane_type)
            queryset = queryset.filter(airplane_type__id__in=airplane_type_ids)

        if self.action == "list":
            return queryset.select_related("airplane_type")

        return queryset

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading image to specific airplane"""
        airplane = self.get_object()
        serializer = self.get_serializer(airplane, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        if self.action in ("retrieve", "update", "partial_update"):
            return RouteDetailSerializer
        return RouteSerializer

    def get_queryset(self):
        """Retrieve the routes with filters"""
        source = self.request.query_params.get("source")
        destination = self.request.query_params.get("destination")

        queryset = self.queryset

        if source:
            source_ids = _params_to_ints(source)
            queryset = queryset.filter(source__id__in=source_ids)

        if destination:
            destination_ids = _params_to_ints(destination)
            queryset = queryset.filter(destination__id__in=destination_ids)

        if self.action in ("list", "retrieve"):
            return queryset.select_related("source", "destination")
        return queryset


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        if self.action in ("retrieve",):
            return FlightDetailSerializer
        return FlightSerializer

    def get_queryset(self):
        """Retrieve the flights with filters"""
        route = self.request.query_params.get("routes")
        airplane = self.request.query_params.get("airplanes")

        queryset = self.queryset

        if route:
            route_ids = _params_to_ints(route)
            queryset = queryset.filter(route__id__in=route_ids)

        if airplane:
            airplane_ids = _params_to_ints(airplane)
            queryset = queryset.filter(airplane__id__in=airplane_ids)

        if self.action in ("list", "retrieve", "update", "create", "partial_update"):
            return queryset.select_related(
                "route__source",
                "route__destination",
                "airplane__airplane_type",
            ).prefetch_related(
                "crewmates",
            )
        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related(
        "tickets__flight__airplane",
        "tickets__flight__route",
        "tickets__flight__crewmates",
    )

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = self.queryset
        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
