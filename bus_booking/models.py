from django.db import models
from users.models import Profile
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
# Create your models here.

DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]


class City(models.Model):
    name = models.CharField(max_length=50, primary_key=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Cities'

class Bus(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    number = models.CharField(max_length=50)
    capacity = models.IntegerField()
    seats_available = ArrayField(models.IntegerField(),default=list)
    fare = models.IntegerField(null=True,blank=True)
    cities = models.ManyToManyField(City, through='Schedule', related_name="buses")

    class Meta:
        verbose_name = 'Bus'
        verbose_name_plural = 'Buses'

    def __str__(self):
        return self.name

class Schedule(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    arrival_time = models.TimeField()
    departure_time = models.TimeField()
    stop_number = models.PositiveIntegerField()

    class Meta:
        ordering = ['bus', 'day']
        constraints = [
            models.UniqueConstraint(
                fields=['bus', 'city', 'day'], 
                name='unique_bus_city_day'
            )
        ]

    def __str__(self):
        return f"{self.bus.name} - {self.city} ({self.day})"

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
                start_idx = self.bus.cities.index(self.from_city)
                end_idx = self.bus.cities.index(self.to_city)
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



class Booking(models.Model):
    STATUS = [
        ('BOOKED', 'Booked'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed')
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    from_city = models.CharField(max_length=50, null=True, blank=True)  # Keep nullable
    to_city = models.CharField(max_length=50, null=True, blank=True)    # Keep nullable
    total_fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    seats = models.PositiveIntegerField(default=1)
    time = models.DateTimeField()
    status = models.CharField(
        max_length=20, 
        choices=STATUS, 
        default='BOOKED'
    )

    def save(self, *args, **kwargs):
        if self._state.adding:  # If this is a new booking
            start_idx = self.bus.cities.index(self.from_city)
            end_idx = self.bus.cities.index(self.to_city)
            
            # Check if enough seats are available
            for i in range(start_idx, end_idx):
                if self.bus.bus_seats_available[i] < self.seats:
                    raise ValidationError("Not enough seats available")
            
            # Update seats
            for i in range(start_idx, end_idx):
                self.bus.bus_seats_available[i] -= self.seats
            self.bus.save()
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking #{self.id} - {self.user.user.username}"
