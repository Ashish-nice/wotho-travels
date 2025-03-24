from django.shortcuts import render
from .models import Bus,Booking,Schedule, Ticket
from django.views.generic import ListView,DetailView
from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse

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
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        passenger_count = int(request.POST.get('passenger_count'))
        
        passenger_names = request.POST.getlist('passenger_name[]')
        passenger_ages = request.POST.getlist('passenger_age[]')
        seat_types = request.POST.getlist('seat_type[]')
        conditioning = request.POST.getlist('conditioning[]')
        

        

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

def checkout(request):
    if request.method == 'POST':
        bus_id = request.POST.get('bus_id')
        from_city = request.POST.get('from_city')
        to_city = request.POST.get('to_city')
        date = request.POST.get('date')
        passenger_count = int(request.POST.get('passenger_count'))
        passenger_names = request.POST.getlist('passenger_name[]')
        passenger_ages = request.POST.getlist('passenger_age[]')
        seat_types = request.POST.getlist('seat_type[]')
        conditioning = request.POST.getlist('conditioning[]')
        print(bus_id)
        bus = Bus.objects.get(id=bus_id)
        
        # Calculate total fare for all passengers
        total_fare = 0
        for i in range(passenger_count):
            fare = calculate_fare(bus, from_city, to_city, seat_types[i], conditioning[i])
            total_fare += fare
        
        # Store booking data in session for later use
        request.session['booking_data'] = {
            'bus_id': bus_id,
            'from_city': from_city,
            'to_city': to_city,
            'date': date,
            'passenger_count': passenger_count,
            'passenger_names': passenger_names,
            'passenger_ages': passenger_ages,
            'seat_types': seat_types,
            'conditioning': conditioning,
            'total_fare': total_fare
        }
        
        return render(request, 'bus_booking/checkout.html', {
            'total_fare': total_fare,
            'passenger_count': passenger_count
        })
    
    # If user refreshes the page, try to get data from session
    booking_data = request.session.get('booking_data', None)
    if booking_data:
        return render(request, 'bus_booking/checkout.html', {
            'total_fare': booking_data['total_fare'],
            'passenger_count': booking_data['passenger_count']
        })
    
    # If no data is available, redirect to home
    return redirect('home')

def calculate_fare(bus, from_city, to_city, seat_type, conditioning):
    try:
        # Get the Schedule objects
        from_schedule = bus.schedule_set.get(city__name=from_city)
        to_schedule = bus.schedule_set.get(city__name=to_city)
        
        # Calculate stops between
        from_stop = from_schedule.stop_number
        to_stop = to_schedule.stop_number
        stops = abs(to_stop - from_stop)
        
        # Base fare calculation
        base_fare = bus.fare
        
        # Additional charges based on seat type
        if seat_type == 'Sleeper':
            seat_charge = stops * 200
        else:  # Seater
            seat_charge = stops * 100
        
        # Additional charges for AC
        ac_charge = 300 if conditioning == 'AC' else 0
        
        # Total fare
        total_fare = base_fare + seat_charge + ac_charge
        
        return total_fare
    except Exception as e:
        print(f"Error calculating fare: {e}")
        return 0

def verify_otp(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        # In a real application, verify OTP against what was sent
        # For demo purposes, accept any 6-digit OTP
        if otp and len(otp) == 6 and otp.isdigit():
            # Get booking data from session
            booking_data = request.session.get('booking_data')
            if booking_data:
                bus = Bus.objects.get(id=booking_data['bus_id'])
                # Create booking
                booking = Booking(
                    ticket_user=request.user.profile,
                    bus=bus,
                    ticket_time=datetime.strptime(booking_data['date'], '%Y-%m-%d'),
                    ticket_fare=booking_data['total_fare'],
                    ticket_status='Booked'
                )
                booking.save()
                
                # Create tickets for each passenger
                for i in range(booking_data['passenger_count']):
                    passenger = Ticket(
                        booking=booking,
                        name=booking_data['passenger_names'][i],
                        age=booking_data['passenger_ages'][i],
                        seat_type=booking_data['seat_types'][i],
                        conditioning=booking_data['conditioning'][i]
                    )
                    passenger.save()
                
                # Clear session data
                del request.session['booking_data']
                
                messages.success(request, 'Booking successful!')
                return redirect('bookings')
        
        messages.error(request, 'Invalid OTP. Please try again.')
    
    return redirect('checkout')

def resend_otp(request):
    # In a real application, generate and send a new OTP
    # For demo purposes, just return a success response
    if request.is_ajax():
        return JsonResponse({'success': True})
    return redirect('checkout')

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

