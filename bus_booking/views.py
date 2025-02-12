from django.shortcuts import render
from .models import Bus
from django.views.generic import ListView,DetailView
from datetime import datetime
# Create your views here.

def home(request):
    return render(request, 'bus_booking/home.html')

class BusListView(ListView):
    model = Bus
    template_name = 'bus_booking/buses.html' # <app>/<model>_<viewtype>.html
    context_object_name = 'buses'
    ordering = ['bus_departure_time']

    def get_queryset(self):
        queryset = Bus.objects.all()
        from_city = self.request.GET.get('from_city')
        to_city = self.request.GET.get('to_city')
        date = self.request.GET.get('date')
        if date:
            date_obj = datetime.strptime(date,'%Y-%m-%d')
            day = date_obj.strftime('%A')
            queryset = queryset.filter(weekly_schedule__contains=[day])
        if from_city and to_city:
            queryset = queryset.filter(bus_route__contains=[from_city,to_city]).all()
            queryset = [bus for bus in queryset if bus.bus_route.index(from_city) < bus.bus_route.index(to_city)]
        
        return queryset
        

class BusDetailView(DetailView):
    model = Bus
    template_name = 'bus_booking/bus_detail.html' # <app>/<model>_<viewtype>.html
