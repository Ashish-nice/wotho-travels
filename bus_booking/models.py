from django.db import models
from users.models import Profile
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
# Create your models here.
class Bus(models.Model):
    bus_id = models.AutoField(primary_key=True)
    bus_name = models.CharField(max_length=50)
    bus_number = models.CharField(max_length=50)
    bus_capacity = models.IntegerField()
    bus_seats_available = ArrayField(models.IntegerField(),default=list)
    base_fare = models.IntegerField(null=True,blank=True)
    bus_duration = models.IntegerField()
    bus_route = ArrayField(models.CharField(max_length=50),default=list)

    class Meta:
        verbose_name = 'Bus'
        verbose_name_plural = 'Buses'

    def __str__(self):
        return self.bus_name

    def save(self, *args, **kwargs):
        if not self.pk:
            self.bus_seats_available = [self.bus_capacity]*(len(self.bus_route)-1)
            super().save(*args, **kwargs)

class RunningSchedule(models.Model):
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='schedules')
    city = models.CharField(max_length=50) 
    arrival_time = models.TimeField(null=True, blank=True)
    departure_time = models.TimeField() 
    running_day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)  
    stop_number = models.PositiveIntegerField()
    trip_number = models.PositiveIntegerField()

    class Meta:
        ordering = ['bus', 'running_day','trip_number', 'stop_number']
        constraints = [
            models.UniqueConstraint(
                fields=['bus', 'city', 'running_day', 'trip_number'], 
                name='unique_bus_city_day'
            )
        ]

    def save(self, *args, **kwargs):
        if self.stop_number == 0 and self.arrival_time is not None:
            raise ValidationError("First stop should not have arrival time")
        if self.stop_number == len(self.bus.bus_route) - 1 and self.departure_time is not None:
            raise ValidationError("Last stop should not have departure time")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.bus.bus_name} - {self.city} ({self.day})"

class BusFare(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='fares')
    from_city = models.CharField(max_length=50)
    to_city = models.CharField(max_length=50)
    fare = models.DecimalField(max_digits=10, decimal_places=2) 
    seat_type = models.CharField(max_length=50, choices=[
        ('General', 'General'),
        ('Luxury', 'Luxury'),
        ('Sleeper', 'Sleeper')
    ])
    conditioning = models.CharField(max_length=50, choices=[
        ('AC', 'AC'),
        ('Non-AC', 'Non-AC')
    ])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['bus', 'from_city', 'to_city','seat_type','conditioning'], name='unique_bus_fare')
        ]

    def __str__(self):
        return f"{self.bus} {self.from_city} → {self.to_city} fare"
    
    def save(self, *args, **kwargs):
        if not self.pk:
            try:
                start_idx = self.bus.bus_route.index(self.from_city)
                end_idx = self.bus.bus_route.index(self.to_city)
                segments = abs(end_idx - start_idx)
                fare = self.base_fare * (segments + 1)
                multipliers = {
                    "General": 1.0,
                    "Luxury": 1.5,
                    "Sleeper": 2.0
                }
                fare *= multipliers.get(self.seat_type, 1.0)
                # AC premium
                if self.conditioning == "AC":
                    fare *= 1.2 
                return int(fare)
            except ValueError:
                raise ValueError("Cities not found in bus route")
        super().save(*args, **kwargs)

    @staticmethod
    def get_fare(bus, from_city, to_city, seat_type, conditioning):
        try:
            fare_obj = BusFare.objects.get(
                bus=bus,
                from_city=from_city,
                to_city=to_city,
                seat_type=seat_type,
                conditioning=conditioning
            )
            return fare_obj.fare
        except BusFare.DoesNotExist:
            # Create new fare if doesn't exist
            fare_obj = BusFare.objects.create(
                bus=bus,
                from_city=from_city,
                to_city=to_city,
                seat_type=seat_type,
                conditioning=conditioning
            )
            return fare_obj.fare


class Booking(models.Model):
    TICKET_STATUS = [
        ('BOOKED', 'Booked'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed')
    ]
    
    ticket_id = models.AutoField(primary_key=True)
    ticket_user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    ticket_bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    from_city = models.CharField(max_length=50, null=True, blank=True)  # Keep nullable
    to_city = models.CharField(max_length=50, null=True, blank=True)    # Keep nullable
    total_fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ticket_seats = models.PositiveIntegerField(default=1)
    ticket_time = models.DateTimeField()
    ticket_status = models.CharField(
        max_length=20, 
        choices=TICKET_STATUS, 
        default='BOOKED'
    )

    def clean(self):
        if not self.from_city or not self.to_city:
            raise ValidationError("Source and destination cities are required")
        
        if self.from_city not in self.ticket_bus.bus_route or \
           self.to_city not in self.ticket_bus.bus_route:
            raise ValidationError("Invalid source or destination city")
        
        if self.ticket_bus.bus_route.index(self.from_city) >= \
           self.ticket_bus.bus_route.index(self.to_city):
            raise ValidationError("Invalid route selection")

    def save(self, *args, **kwargs):
        self.clean()
        if self._state.adding:  # If this is a new booking
            start_idx = self.ticket_bus.bus_route.index(self.from_city)
            end_idx = self.ticket_bus.bus_route.index(self.to_city)
            
            # Check if enough seats are available
            for i in range(start_idx, end_idx):
                if self.ticket_bus.bus_seats_available[i] < self.ticket_seats:
                    raise ValidationError("Not enough seats available")
            
            # Update seats
            for i in range(start_idx, end_idx):
                self.ticket_bus.bus_seats_available[i] -= self.ticket_seats
            self.ticket_bus.save()
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking #{self.ticket_id} - {self.ticket_user.user.username}"
