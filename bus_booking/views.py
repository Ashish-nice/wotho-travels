from django.shortcuts import render
from .models import Bus,Booking,Ticket,City,Journey,Schedule
from django.views.generic import ListView,DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta, datetime
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from .utils import generate_otp,send_booking_otp
from django.db import transaction
from django.contrib.auth.decorators import login_required

# Create your views here.
def home(request):
    return render(request, 'bus_booking/home.html')

class RouteParamsMixin:
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.from_city = request.GET.get('from_city').lower()
        self.to_city = request.GET.get('to_city').lower()
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
        date_obj = datetime.strptime(self.date, "%Y-%m-%d").date()
        if(Journey.objects.filter(schedule=from_schedule,date=date_obj-timedelta(days=date_obj.isoweekday()%7)).exists()):
            available_seats=Journey.objects.get(schedule=from_schedule,date=date_obj-timedelta(days=date_obj.isoweekday()%7)).seats
        else:
            available_seats=self.object.capacity
        print(available_seats)
        for i in range (from_schedule.stop_number, to_schedule.stop_number+1):
            if(Journey.objects.filter(schedule=from_schedule,date=date_obj-timedelta(days=date_obj.isoweekday()%7)).exists()):
                available_seats = min(available_seats, Journey.objects.get(schedule=self.object.schedule_set.get(stop_number=i),date=date_obj-timedelta(days=date_obj.isoweekday()%7)).seats)
        context.update({
                'departure_time': from_schedule.departure_time,
                'arrival_time': to_schedule.arrival_time,
                'departure_day': from_schedule.day,
                'arrival_day': to_schedule.day,
                'available_seats': available_seats,
                'date': self.date
        })
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        passenger_count = int(request.POST.get('passenger_count'))
        passenger_names = request.POST.getlist('passenger_name[]')
        passenger_ages = request.POST.getlist('passenger_age[]')
        seat_types = request.POST.getlist('seat_type[]')
        conditioning = request.POST.getlist('conditioning[]')
        
        # Redirect to checkout with form data
        return redirect(f'/checkout/?bus_id={self.object.id}&from_city={self.from_city}&to_city={self.to_city}&date={self.date}&passenger_count={passenger_count}&passenger_names={",".join(passenger_names)}&passenger_ages={",".join(passenger_ages)}&seat_types={",".join(seat_types)}&conditioning={",".join(conditioning)}')

@login_required
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
        
        bus = Bus.objects.get(id=bus_id)
        
        # Calculate total fare for all passengers
        total_fare = 0
        base_fare = 0
        taxes = 0
        
        for i in range(passenger_count):
            fare = calculate_fare(bus, from_city, to_city, seat_types[i], conditioning[i])
            base_fare += fare
        
        taxes = base_fare*0.18
        total_fare = base_fare+taxes
        
        # Store booking data in session for later use (without OTP at this point)
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
            'total_fare': float(total_fare),
            'base_fare': float(base_fare),
            'taxes': float(taxes)
        }
        return render(request, 'bus_booking/checkout.html', {
            'total_fare': total_fare,
            'base_fare': base_fare,
            'taxes': taxes,
            'passenger_count': passenger_count,
            'email': request.user.email,
            'wallet_balance': request.user.profile.user_wallet
        })
    
    # If user refreshes the page, try to get data from session
    booking_data = request.session.get('booking_data', None)
    if booking_data:
        return render(request, 'bus_booking/checkout.html', {
            'total_fare': booking_data['total_fare'],
            'base_fare': booking_data['base_fare'],
            'taxes': booking_data['taxes'],
            'passenger_count': booking_data['passenger_count'],
            'email': request.user.email,
            'wallet_balance': request.user.profile.user_wallet
        })
    
    # If no data is available, redirect to home
    return redirect('home')

@login_required
def transact(request):
    print(request.method)
    if request.method == 'POST':
        # Get booking data from session
        booking_data = request.session.get('booking_data')
        if not booking_data:
            messages.error(request, 'Booking session expired. Please try again.')
            return redirect('home')
        if request.user.profile.user_wallet < booking_data['total_fare']:
            messages.error(request, 'Insufficient balance in wallet. Please recharge and try again.')
            return redirect('checkout')
        # Generate and send OTP
        otp = generate_otp()
        email_sent = send_booking_otp(request.user.email, otp)
        
        if not email_sent:
            messages.error(request, 'Failed to send OTP. Please try again.')
            return redirect('home')
        
        # Add OTP to booking data in session
        booking_data['otp'] = otp
        booking_data['otp_date_time'] = datetime.now().timestamp()
        request.session['booking_data'] = booking_data       
            
        Booking.objects.get_or_create(
                user=request.user.profile,
                bus=Bus.objects.get(id=booking_data['bus_id']),
                from_city=City.objects.get(name=booking_data['from_city']),
                to_city=City.objects.get(name=booking_data['to_city']),
                total_fare=booking_data['total_fare'],
                seats=booking_data['passenger_count'],
                journey_date=datetime.combine(datetime.strptime(booking_data['date'],'%Y-%m-%d'),Schedule.objects.get(bus=Bus.objects.get(id=booking_data['bus_id']),city=City.objects.get(name=booking_data['from_city'])).arrival_time),
                booking_date=timezone.now(),
                otp=booking_data['otp'],
            )
        for i in range(booking_data['passenger_count']):
            Ticket.objects.get_or_create(
                booking=Booking.objects.get(otp=booking_data['otp']),
                name=booking_data['passenger_names'][i],
                age=booking_data['passenger_ages'][i],
                seat_type=booking_data['seat_types'][i],
                conditioning=booking_data['conditioning'][i],
            )
        return render(request, 'bus_booking/transaction.html', {
            'total_fare': booking_data['total_fare'],
            'base_fare': booking_data['base_fare'],
            'taxes': booking_data['taxes'],
            'email': request.user.email,
        })
    
    # If user tries to access this page directly, redirect to checkout
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
            seat_charge = stops * 400
        else:  # Seater
            seat_charge = stops * 300
        
        # Additional charges for AC
        ac_charge = 400 if conditioning == 'AC' else 0
        
        # Total fare
        total_fare = base_fare*stops + seat_charge + ac_charge
        
        return total_fare
    except Exception as e:
        print(f"Error calculating fare: {e}")
        return 0

def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        booking_data = request.session.get('booking_data')
        
        if not booking_data:
            messages.error(request, 'Booking session expired. Please try again.')
            return redirect('home')
        
        # Check OTP expiration (10 minutes)
        otp_age = datetime.now().timestamp() - booking_data['otp_date_time']
        if otp_age > 300:  # 600 seconds = 10 minutes
            messages.error(request, 'OTP expired. Please request a new one.')
            return redirect('transact')
        print(entered_otp)
        print(booking_data['otp'])
        if int(entered_otp)==int(booking_data['otp']):
            try:
                with transaction.atomic():
                    profile = request.user.profile
                    profile.user_wallet -= booking_data['total_fare']
                    profile.save()
                    # Get bus and cities
                    bus = Bus.objects.get(id=booking_data['bus_id'])
                    from_stop = bus.schedule_set.get(city=booking_data['from_city']).stop_number
                    to_stop = bus.schedule_set.get(city=booking_data['to_city']).stop_number   

                    for i in range(from_stop, to_stop+1):
                        schedule = bus.schedule_set.get(stop_number=i)
                        print(booking_data['date'])
                        date = datetime.strptime(booking_data['date'], '%Y-%m-%d')
                        journey, created = Journey.objects.get_or_create(schedule=schedule,date=date-timedelta(days=date.isoweekday()%7))
                        print(booking_data['passenger_count'])
                        journey.seats -= booking_data['passenger_count']
                        journey.save()  

                    booking=Booking.objects.get(otp=entered_otp)
                    booking.booking_payment = True
                    booking.save()

                    for i in range(booking_data['passenger_count']):
                        ticket = booking.tickets.get(name=booking_data['passenger_names'][i])
                        ticket.ticket_payment = True
                        ticket.save() 

                    request.session['confirmed_booking_id'] = booking.id

                # Clear session after successful booking
                del request.session['booking_data']
                messages.success(request, 'Booking confirmed successfully!')
                print('Booking successful')
                return redirect('transaction_success')
            except Exception as e:
                messages.error(request, f'Error processing booking: {str(e)}')
                print('Booking failed, OTP verified')
                return redirect('transact')
        
        messages.error(request, 'Invalid OTP. Please try again.')
        print('Booking failed, OTP not verified')
    return redirect('transact')

def resend_otp(request):
    if request.method == 'POST':
        booking_data = request.session.get('booking_data')
        if booking_data:
            # Generate new OTP
            new_otp = generate_otp()
            booking_data['otp'] = new_otp
            request.session['booking_data'] = booking_data
            
            # In a real application, send this new OTP to user's email or phone
            return JsonResponse({
                'success': True, 
                'message': 'OTP has been resent to your email',
                'otp': new_otp  # In production, remove this
            })
    
    return JsonResponse({'success': False, 'message': 'Error resending OTP'})

@login_required
def cancel_booking(request, booking_id):
    if request.method == 'POST':
        try:
            booking = Booking.objects.get(id=booking_id)
            current_time = timezone.now()
            print(current_time)
            if booking.booking_payment == False:
                booking.delete()
                return JsonResponse({
                    'success': True,
                    'message': 'Unpaid booking deleted successfully'
                })
            else:    
                if current_time + timedelta(hours=6) < booking.journey_date:
                    with transaction.atomic():
                        profile = request.user.profile
                        if current_time + timedelta(hours=12) > booking.journey_date:
                            profile.user_wallet += 0.75*booking.total_fare
                        else:
                            profile.user_wallet += booking.total_fare
                        profile.save()  # Save the updated wallet amount
                        bus = booking.bus
                        from_stop = bus.schedule_set.get(city=booking.from_city).stop_number
                        to_stop = bus.schedule_set.get(city=booking.to_city).stop_number
                        # Get journey date
                        travel_date = booking.journey_date.date()
                        # Update all journeys along the route
                        for i in range(from_stop, to_stop + 1):
                            schedule = bus.schedule_set.get(bus=bus,stop_number=i)
                            journey = Journey.objects.get(
                                schedule=schedule,
                                date=travel_date-timedelta(days=travel_date.isoweekday()%7)
                            )
                            journey.seats += booking.seats
                            journey.save()                                                
                        booking.delete()
                    return JsonResponse({
                        'success': True,
                        'message': 'Booking cancelled successfully, check your wallet for refunded amount'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'Bookings can only be cancelled 6 hours before departure'
                    })

        except Booking.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Booking not found or you do not have permission to cancel it'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    return redirect('bookings')

@login_required
def transaction_success(request):
    booking_id = request.session.get('confirmed_booking_id')
    if booking_id:
        booking = Booking.objects.get(id=booking_id)
        tickets = booking.tickets.all()
        context = {
                'booking': booking,
                'tickets': tickets,
                'total_fare': booking.total_fare,
                'from_city': booking.from_city,
                'to_city': booking.to_city,
                'passenger_count': booking.seats
            }
        del request.session['confirmed_booking_id']
        return render(request, 'bus_booking/transaction_success.html',context)
    
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
            user=self.request.user.profile,
            journey_date__gt=current_time
        ).order_by('journey_date')
        context['past_bookings'] = Booking.objects.filter(
            user=self.request.user.profile,
            journey_date__lte=current_time
        ).order_by('-journey_date')
        
        return context

class TicketView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'bus_booking/tickets.html'
    context_object_name = 'tickets'

    def get_queryset(self):
        booking_id = self.kwargs.get('booking_id')
        if booking_id:
            try:
                booking = Booking.objects.get(
                    id=booking_id, 
                    user=self.request.user.profile
                )
                return Ticket.objects.filter(booking=booking)
            except Booking.DoesNotExist:
                messages.error(self.request, "Booking not found or you don't have permission to view these tickets")
                return Ticket.objects.none()
        else:
            return Ticket.objects.none()

def city_autocomplete(request):
    term = request.GET.get('term', '')
    cities = City.objects.filter(name__icontains=term).values_list('name', flat=True)[:10]
    return JsonResponse(list(cities), safe=False)
