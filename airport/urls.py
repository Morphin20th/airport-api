from django.urls import path, include
from rest_framework import routers

from airport.views import (
    AirplaneViewSet,
    AirplaneTypeViewSet,
    AirportViewSet,
    RouteViewSet,
    CrewViewSet,
    FlightViewSet,
)

router = routers.DefaultRouter()
router.register("airplane-types", AirplaneTypeViewSet)
router.register("airplanes", AirplaneViewSet)
router.register("airports", AirportViewSet)
router.register("routes", RouteViewSet)
router.register("crewmates", CrewViewSet)
router.register("flights", FlightViewSet)

urlpatterns = [
    path("", include(router.urls))
]

app_name = "airport"
