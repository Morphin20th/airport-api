from django.contrib import admin

from airport.models import Airplane, AirplaneType

admin.site.register(Airplane)
admin.site.register(AirplaneType)