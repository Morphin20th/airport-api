from django.contrib import admin

from airport.models import (
    Airplane,
    AirplaneType,
    Airport,
    Route,
    Flight,
    Crew
)

admin.site.register(Airplane)
admin.site.register(AirplaneType)
admin.site.register(Airport)
admin.site.register(Route)
admin.site.register(Flight)
admin.site.register(Crew)
