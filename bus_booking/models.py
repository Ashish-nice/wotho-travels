from django.db import models
from users.models import Profile
from django.contrib.postgres.fields import ArrayField
# Create your models here.
class Bus(models.Model):
    bus_id = models.AutoField(primary_key=True)
    bus_name = models.CharField(max_length=50)
    bus_number = models.CharField(max_length=50)
    bus_capacity = models.IntegerField()
    bus_seats_available = models.IntegerField(null=True,blank=True)
    bus_fare = models.IntegerField()
    
    weekly_schedule = ArrayField(models.CharField(max_length=10, choices=[
            ('Monday', 'Monday'),
            ('Tuesday', 'Tuesday'),
            ('Wednesday', 'Wednesday'),
            ('Thursday', 'Thursday'),
            ('Friday', 'Friday'),
            ('Saturday', 'Saturday'),
            ('Sunday', 'Sunday'),
        ]),
        blank=True,
        null=True,
        default=list)
    bus_duration = models.IntegerField()
    bus_route = ArrayField(models.CharField(max_length=50),default=list)
    class Meta:
        verbose_name = 'Bus'
        verbose_name_plural = 'Buses'
    def __str__(self):
        return self.bus_name
    def save(self, *args, **kwargs):
        self.bus_seats_available = self.bus_capacity
        super().save(*args, **kwargs)
    
class Booking(models.Model):
    ticket_id = models.AutoField(primary_key=True)
    ticket_user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    ticket_bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    ticket_seats = models.IntegerField()
    ticket_total_fare = models.IntegerField()
    ticket_time = models.DateTimeField()
    ticket_status = models.CharField(max_length=50)
    def __init__(self):
        self.ticket_status = "Booked"
        self.ticket_total_fare = self.ticket_seats * self.ticket_bus.bus_fare
        self.ticket_date = self.ticket_bus.bus_departure_time
    def __str__(self):
        return self.ticket_id