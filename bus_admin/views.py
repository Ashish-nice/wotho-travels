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

@method_decorator(group_required('bus_admin'), name='dispatch')
class UpdateBusView(View):
    def post(self, request, bus_id, *args, **kwargs):
        try:
            bus = get_object_or_404(Bus, id=bus_id, manager=request.user.profile)
            data = json.loads(request.body)
            
            bus.name = data.get('name', bus.name)
            bus.number = data.get('number', bus.number)
            bus.capacity = int(data.get('capacity', bus.capacity))
            bus.fare = float(data.get('fare', bus.fare))
            bus.save()
            schedules = data.get('schedules', [])

            if schedules:
                with transaction.atomic():
                    Schedule.objects.filter(bus=bus).delete()
                    for i, schedule in enumerate(schedules, 1):
                        city, created = City.objects.get_or_create(name=schedule['city'])
                        Schedule.objects.create(
                            bus=bus,
                            city=city,
                            stop_number=i,
                            arrival_time=schedule['arrivalTime'],
                            departure_time=schedule['departureTime'],
                            day=schedule['day']
                        )
            
            return JsonResponse({'success': True, 'message': 'Bus updated successfully',})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
        
@method_decorator(group_required('bus_admin'), name='dispatch')
class CancelBusView(View):
    def post(self, request, bus_id, *args, **kwargs):
        try:
            bus = get_object_or_404(Bus, id=bus_id, manager=request.user.profile)
            if request.body:
                try:
                    data = json.loads(request.body)
                except json.JSONDecodeError:
                    data = {}
            else:
                data = request.POST           
            # Get all future bookings for this bus
            future_bookings = Booking.objects.filter(
                bus=bus,
                journey_date__gte=timezone.now(),
                booking_payment=True,
                status='BOOKED'  # Only process active bookings
            )
            
            refund_count = 0
            with transaction.atomic():
                for booking in future_bookings:
                    # Refund the full amount to the user's wallet
                    profile = booking.user
                    profile.user_wallet += booking.total_fare
                    profile.save()
                    
                    # Mark booking as cancelled
                    booking.status = 'CANCELLED'
                    booking.save()
                    
                    # Update seat availability in journeys
                    try:
                        from_stop = bus.schedule_set.get(city=booking.from_city).stop_number
                        to_stop = bus.schedule_set.get(city=booking.to_city).stop_number
                        travel_date = booking.journey_date.date()
                        
                        for i in range(from_stop, to_stop + 1):
                            try:
                                schedule = bus.schedule_set.get(stop_number=i)
                                journey, created = Journey.objects.get_or_create(
                                    schedule=schedule,
                                    date=travel_date
                                )
                                journey.seats += booking.seats
                                journey.save()
                            except Schedule.DoesNotExist:
                                continue
                    except Exception as e:
                        print(f"Error updating journey for booking {booking.id}: {str(e)}")
                        continue
                    
                    refund_count += 1
                
                # Delete the bus instead of just marking it inactive
                bus_id = bus.id
                bus_name = bus.name
                bus.delete()
            
            # Return success response that will work with the template's JavaScript
            return JsonResponse({
                'success': True,
                'message': f'Bus "{bus_name}" deleted successfully. {refund_count} bookings were refunded.',
                'refund_count': refund_count,
                'bus_id': bus_id
            })
            
        except Exception as e:
            # Log the exception details
            print(f"Error cancelling bus: {str(e)}")
            return JsonResponse({'success': False, 'message': f'Error cancelling bus: {str(e)}'}, status=500)

@method_decorator(group_required('bus_admin'), name='dispatch')
class GetBusScheduleView(View):
    def get(self, request, bus_id, *args, **kwargs):
        try:
            bus = get_object_or_404(Bus, id=bus_id, manager=request.user.profile)
            schedules = Schedule.objects.filter(bus=bus).order_by('stop_number')
            
            schedule_data = []
            for schedule in schedules:
                schedule_data.append({
                    'stopNumber': schedule.stop_number,
                    'city': schedule.city.name,
                    'arrivalTime': schedule.arrival_time.strftime('%I:%M %p') if schedule.arrival_time else '',
                    'departureTime': schedule.departure_time.strftime('%I:%M %p') if schedule.departure_time else '',
                    'day': schedule.day
                })
            
            return JsonResponse({
                'success': True,
                'bus': {
                    'id': bus.id,
                    'name': bus.name,
                    'number': bus.number
                },
                'schedules': schedule_data
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)