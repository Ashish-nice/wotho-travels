from django.contrib import admin
from .models import Bus, Ticket
# Register your models here.
@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('bus_name', 'bus_number', 'bus_departure_time', 'bus_seats_available')
    list_filter = ('bus_departure_time',)
    search_fields = ('bus_name', 'bus_number')

admin.site.register(Ticket)