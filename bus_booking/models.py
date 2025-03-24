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
SEAT_TYPES = [
    ('Seater','Seater'),
    ('Sleeper','Sleeper'),
    ]
CONDITIONING = [
    ('AC','AC'),
    ('Non-AC','Non-AC'),
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
    seats = models.IntegerField(null=True, blank=True)
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
    
    def save(self, *args, **kwargs):
        if self.seats is None:
            self.seats = self.bus.capacity
        super().save(*args, **kwargs)

class Ticket(models.Model):
    name = models.CharField(max_length=50)
    age = models.PositiveIntegerField()
    seat_type = models.CharField(max_length=8,choices=SEAT_TYPES)
    conditioning = models.CharField(max_length=12,choices=CONDITIONING)

class Booking(models.Model):
    STATUS = [
        ('BOOKED', 'Booked'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed')
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    from_city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="departures")
    to_city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="arrivals")    
    total_fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    seats = models.PositiveIntegerField(default=1)
    date_time = models.DateTimeField()
    status = models.CharField(
        max_length=20, 
        choices=STATUS, 
        default='BOOKED'
    )

