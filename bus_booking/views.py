from django.shortcuts import render
from .models import Bus,Booking,BusFare,Schedule
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

class BusListView(ListView):
    model = Bus
    template_name = 'bus_booking/buses.html' # <app>/<model>_<viewtype>.html
    context_object_name = 'buses'
    length = 0

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.from_city = request.GET.get('from_city')
        self.to_city = request.GET.get('to_city')
        self.date = request.GET.get('date')

    def get_queryset(self):
        queryset = Bus.objects.all()
        if self.date:
            date_obj = datetime.strptime(self.date,'%Y-%m-%d')
            day = date_obj.strftime('%A')
            queryset = queryset.filter(schedule__day=day).all()
        for bus in queryset:
            from_stop = bus.schedule_set.get(city=self.from_city).stop_number
            to_stop = bus.schedule_set.get(city=self.to_city).stop_number
            if from_stop > to_stop:
                queryset.exclude(bus_id=bus.bus_id)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['from_city'] = self.from_city
        context['to_city'] = self.to_city
        context['date'] = self.date
        return context

class BusDetailView(LoginRequiredMixin, DetailView):
    model = Bus
    template_name = 'bus_booking/bus_detail.html' # <app>/<model>_<viewtype>.html
    context_object_name = 'bus'
    login_url = 'login'  # URL name for your login view
    redirect_field_name = 'next'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['from_city'] = self.request.GET.get('from_city')
        context['to_city'] = self.request.GET.get('to_city')
        context['date'] = self.request.GET.get('date')
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
        
        # Get upcoming and past bookings
        context['upcoming_bookings'] = Booking.objects.filter(
            ticket_user=self.request.user.profile,
            ticket_time__gt=current_time
        ).order_by('ticket_time')
        
        context['past_bookings'] = Booking.objects.filter(
            ticket_user=self.request.user.profile,
            ticket_time__lte=current_time
        ).order_by('-ticket_time')
        
        return context

def book(request, bus_id):
    if request.method == 'POST':
        try:
            bus = Bus.objects.get(bus_id=bus_id)
            from_city = request.POST.get('from_city')
            to_city = request.POST.get('to_city')
            ticket_seats = int(request.POST.get('ticket_seats'))
            ticket_time = datetime.strptime(request.POST.get('ticket_time'), '%Y-%m-%dT%H:%M')
            seat_type = request.POST.get('seat_type')
            conditioning = request.POST.get('conditioning')
            
            if ticket_seats <= 0:
                messages.error(request, 'Number of seats should be greater than 0')
                return redirect('bus_detail', pk=bus_id)
            
            # Check if the booking time is in the future
            if ticket_time <= timezone.now():
                messages.error(request, 'Cannot book for past time')
                return redirect('bus_detail', pk=bus_id)
            
            # Calculate fare
            fare = BusFare.get_or_create(bus, from_city, to_city, seat_type, conditioning)
            
            # Create and save the booking
            booking = Booking(
                user=request.user.profile,
                bus=bus,
                from_city=from_city,
                to_city=to_city,
                fare=fare,
                seats=ticket_seats,
                time=ticket_time,
                status='BOOKED'
            )
            booking.save()
            
            messages.success(request, f'Successfully booked {ticket_seats} seats')
            return redirect('bookings')
            
        except Bus.DoesNotExist:
            messages.error(request, 'Bus not found')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Booking failed: {str(e)}')
    
    return redirect('bus_detail', pk=bus_id)

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

