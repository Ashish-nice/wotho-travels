from django.shortcuts import render
from .models import Bus,Booking,Schedule
from django.views.generic import ListView,DetailView
from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Q
# Create your views here.

def home(request):
    return render(request, 'bus_booking/home.html')

class RouteParamsMixin:
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.from_city = request.GET.get('from_city')
        self.to_city = request.GET.get('to_city')
        self.date = request.GET.get('date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['from_city'] = self.from_city
        context['to_city'] = self.to_city
        context['date'] = self.date
        return context

class BusListView(RouteParamsMixin, ListView):
    model = Bus
    template_name = 'bus_booking/buses.html' # <app>/<model>_<viewtype>.html
    context_object_name = 'buses'
    length = 0

    def get_queryset(self):
        queryset = Bus.objects.all()
        queryset = queryset.filter(schedule__city__name=self.from_city).all()
        queryset = queryset.filter(schedule__city__name=self.to_city).all()
        if self.date:
            date_obj = datetime.strptime(self.date,'%Y-%m-%d')
            day = date_obj.strftime('%A')
            queryset = queryset.filter(
            schedule__city__name=self.from_city,
            schedule__day=day).all()
        for bus in queryset:
            from_stop = bus.schedule_set.get(city=self.from_city).stop_number
            to_stop = bus.schedule_set.get(city=self.to_city).stop_number
            if from_stop > to_stop:
                queryset=queryset.exclude(id=bus.id)
        return queryset

class BusDetailView(RouteParamsMixin, LoginRequiredMixin, DetailView):
    model = Bus
    template_name = 'bus_booking/bus_detail.html'
    context_object_name = 'bus'
    login_url = 'login'
    redirect_field_name = 'next'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from_schedule = self.object.schedule_set.get(
            city__name=self.from_city,
        )
        to_schedule = self.object.schedule_set.get(
            city__name=self.to_city
        )
        available_seats = from_schedule.seats
        print(available_seats)
        for i in range (from_schedule.stop_number, to_schedule.stop_number):
            available_seats = min(available_seats, self.object.schedule_set.get(stop_number=i).seats)

        context.update({
                'departure_time': from_schedule.departure_time,
                'arrival_time': to_schedule.arrival_time,
                'departure_day': from_schedule.day,
                'arrival_day': to_schedule.day,
                'available_seats': available_seats,
        })
        return context
            

class UserBookingsView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bus_booking/bookings.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_time = timezone.now()
        context['upcoming_bookings'] = Booking.objects.filter(
            ticket_user=self.request.user.profile,
            ticket_time__gt=current_time
        ).order_by('ticket_time')
        context['past_bookings'] = Booking.objects.filter(
            ticket_user=self.request.user.profile,
            ticket_time__lte=current_time
        ).order_by('-ticket_time')
        
        return context

def calculate_fare(bus, from_city, to_city, seat_type, conditioning):
    from_stop = bus.schedule_set.get(city=from_city).stop_number
    to_stop = bus.schedule_set.get(city=to_city).stop_number
    stops = abs(from_stop - to_stop) + 1
    
    if seat_type == 'Sleeper':
        fare = stops * 1000 + bus.fare
    else:
        fare = stops * 500 + bus.fare
    
    if conditioning == 'AC':
        fare += 500
    
    return fare

def book(request, id):
    if request.method == 'POST':
        try:
            bus = Bus.objects.get(id=id)
            from_city = request.POST.get('from_city')
            to_city = request.POST.get('to_city')
            ticket_time = datetime.strptime(request.POST.get('ticket_time'), '%H:%M')
            
            passenger_names = request.POST.getlist('passenger_name[]')
            passenger_ages = request.POST.getlist('passenger_age[]')
            seat_types = request.POST.getlist('seat_type[]')
            conditioning_types = request.POST.getlist('conditioning[]')
            
            total_seats = len(passenger_names)
            
            if total_seats <= 0:
                messages.error(request, 'At least one passenger is required')
                return redirect('bus_detail', pk=id)
            
            # Check if the booking time is in the future
            if ticket_time <= timezone.now():
                messages.error(request, 'Cannot book for past time')
                return redirect('bus_detail', pk=id)
            
            # Calculate total fare
            total_fare = 0
            for i in range(total_seats):
                fare = calculate_fare(bus, from_city, to_city, seat_types[i], conditioning_types[i])
                total_fare += fare
            
            # Create and save the booking
            booking = Booking(
                user=request.user.profile,
                bus=bus,
                from_city=from_city,
                to_city=to_city,
                fare=total_fare,
                seats=total_seats,
                time=ticket_time,
                status='BOOKED',
                passenger_details={
                    'names': passenger_names,
                    'ages': passenger_ages,
                    'seat_types': seat_types,
                    'conditioning': conditioning_types
                }
            )
            booking.save()
            
            messages.success(request, f'Successfully booked {total_seats} seats')
            return redirect('bookings')
            
        except Bus.DoesNotExist:
            messages.error(request, 'Bus not found')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Booking failed: {str(e)}')
    
    return redirect('bus_detail', pk=id)

def cancel_booking(request, booking_id):
    if request.method == 'POST':
        booking = Booking.objects.get(ticket_id=booking_id)
        current_time = timezone.now()
        
        if current_time + timedelta(hours=6) < booking.ticket_time:
            booking.ticket_status = 'Cancelled'
            booking.save()
            messages.success(request, 'Booking cancelled successfully')
        else:
            messages.error(request, 'Bookings can only be cancelled 6 hours before departure')
    
    return redirect('bookings')

