from django.contrib.auth.models import Group
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, get_object_or_404
from django.views.generic.edit import FormView
from django.views import View
from django.views.generic import ListView
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.db import transaction
from bus_booking.models import Bus, Booking, Schedule, City, Journey
from datetime import datetime, timedelta
from django.utils import timezone
import json

#Creating my own decorator to check if the user is authenticated and in the BusAdmin group
def group_required(*groups):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.groups.filter(name__in=groups).exists():
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, 'You are not authorized to access this section.')
                    return render(request, 'bus_admin/login.html')
            else:
                messages.error(request, 'You need to log in first.')
                return render(request, 'bus_admin/login.html')
        return _wrapped_view
    return decorator

# Create your views here.
class BusAdminLoginView(FormView):
    template_name = 'bus_admin/login.html'
    form_class = AuthenticationForm
    success_url = '/bus-admin/dashboard/'  

    def form_valid(self, form):
        user = form.get_user()
        if user.groups.filter(name='bus_admin').exists():
            return super().form_valid(form)
        else:
            messages.error(self.request, 'You are not authorized to access this section.')
            return render(self.request,'bus_admin/login.html', {'form': form})
        
@method_decorator(group_required('bus_admin'), name='dispatch')
class BusAdminDashboardView(View):
    template_name = 'bus_admin/dashboard.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

@method_decorator(group_required('bus_admin'), name='dispatch')
class BusListView(ListView):
    template_name = 'bus_admin/bus_list.html'
    model = Bus
    context_object_name = 'buses'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(manager=self.request.user.profile)
        return queryset
    
@method_decorator(group_required('bus_admin'), name='dispatch')
class BookingListView(ListView):
    template_name = 'bus_admin/booking_list.html'
    model = Booking
    context_object_name = 'bookings'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter()
        return Booking.objects.filter(bus__manager=self.request.user.profile)

@method_decorator(group_required('bus_admin'), name='dispatch')
class AddBusView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            name = data.get('name')
            number = data.get('number')
            capacity = data.get('capacity')
            fare = data.get('fare')
            description = data.get('description', '')
            
            if not all([name, number, capacity, fare]):
                return JsonResponse({'success': False, 'message': 'All fields are required'}, status=400)
            
            new_bus = Bus.objects.create(
                name=name,
                number=number,
                capacity=int(capacity),
                fare=float(fare),
                manager=request.user.profile
            )
            
            return JsonResponse({
                'success': True, 
                'message': 'Bus added successfully',
                'bus': {
                    'id': new_bus.id,
                    'name': new_bus.name,
                    'number': new_bus.number,
                    'capacity': new_bus.capacity,
                    'fare': new_bus.fare
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

