from datetime import datetime

from django.db.models import Count
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
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


def _params_to_ints(qs):
    """Converts a list of string IDs to a list of integers"""
    return [int(str_id) for str_id in qs.split(",")]


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="name",
                type=str,
                description="Filter by name (e.g., ?name=Boeing)",
            ),
            OpenApiParameter(
                name="airplane-type",
                type={"type": "array", "items": {"type": "number"}},
                description="Filter by airplane type IDs (e.g., ?airplane-type=1,3)",
            ),
        ]
    )
)
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
            queryset = queryset.select_related("airplane_type")

        return queryset.distinct()

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


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="source",
                type={"type": "array", "items": {"type": "number"}},
                description="Filter by source IDs (e.g., ?source=1,3)",
            ),
            OpenApiParameter(
                name="destination",
                type={"type": "array", "items": {"type": "number"}},
                description="Filter by destination IDs (e.g., ?destination=1,3)",
            ),
        ]
    )
)
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
            queryset = queryset.select_related("source", "destination")
        return queryset.distinct()


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="routes",
                type={"type": "array", "items": {"type": "number"}},
                description="Filter by route IDs (e.g., ?routes=1,3)",
            ),
            OpenApiParameter(
                name="airplanes",
                type={"type": "array", "items": {"type": "number"}},
                description="Filter by airplane IDs (e.g., ?airplanes=1,3)",
            ),
            OpenApiParameter(
                name="departure-date",
                type=str,
                description="Filter by departure date in "
                            "YYYY-MM-DD format (e.g., ?departure-date=2024-10-08)",
            )
        ]
    )
)
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
        departure_date = self.request.query_params.get("departure-date")

        queryset = self.queryset.select_related(
            "route__source",
            "route__destination",
            "airplane__airplane_type",
        ).prefetch_related(
            "crewmates",
        )

        if route:
            route_ids = _params_to_ints(route)
            queryset = queryset.filter(route__id__in=route_ids)

        if airplane:
            airplane_ids = _params_to_ints(airplane)
            queryset = queryset.filter(airplane__id__in=airplane_ids)

        if departure_date:
            date = datetime.strptime(departure_date, "%Y-%m-%d").date()
            queryset = queryset.filter(departure_time__date=date)

        if self.action == "list":
            queryset = queryset.annotate(occupied_seats=Count("tickets"))

        return queryset.distinct()


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
