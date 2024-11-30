from django.urls import path, include
from rest_framework import routers

from airport.views import AirplaneViewSet, AirplaneTypeViewSet

router = routers.DefaultRouter()
router.register("airplanes", AirplaneViewSet)
router.register("airplane-types", AirplaneTypeViewSet)

urlpatterns = [
    path("", include(router.urls))
]

app_name = "airport"
