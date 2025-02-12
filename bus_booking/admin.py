from django.contrib import admin
from .models import Bus, Booking
# Register your models here.
@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('bus_name', 'bus_number', 'bus_seats_available')
    search_fields = ('bus_name', 'bus_number')

    def clean_bus_route(self):
        value = self.cleaned_data['bus_route']
        return value.split(',') if value else []
   
    def clean_weekly_schedule(self):
        value = self.cleaned_data['weekly_schedule']
        return value.split(',') if value else []

admin.site.register(Booking)