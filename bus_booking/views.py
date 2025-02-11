from .models import Bus
from django.views.generic import ListView
# Create your views here.

class BusListView(ListView):
    model = Bus
    template_name = 'bus_booking/home.html' # <app>/<model>_<viewtype>.html
    context_object_name = 'buses'
    ordering = ['bus_departure_time']

class BusDetailView(ListView):
    model = Bus
    template_name = 'bus_booking/bus_detail.html' # <app>/<model>_<viewtype>.html
    context_object_name = 'buses'
