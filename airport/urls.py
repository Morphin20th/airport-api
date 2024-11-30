from django.urls import path, include
from rest_framework import routers

from airport.views import (
    AirplaneViewSet,
    AirplaneTypeViewSet,
    AirportViewSet,
    RouteViewSet,
    CrewViewSet,
)

router = routers.DefaultRouter()
router.register("airplanes", AirplaneViewSet)
router.register("airplane-types", AirplaneTypeViewSet)
router.register("airports", AirportViewSet)
router.register("routes", RouteViewSet)
router.register("crewmates", CrewViewSet)

urlpatterns = [
    path("", include(router.urls))
]

app_name = "airport"
