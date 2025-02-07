from django.db import models
from users.models import Profile
# Create your models here.
class Bus(models.Model):
    bus_id = models.AutoField(primary_key=True)
    bus_name = models.CharField(max_length=50)
    bus_number = models.CharField(max_length=50)
    bus_capacity = models.IntegerField()
    bus_seats_available = models.IntegerField()
    bus_fare = models.IntegerField()
    bus_departure_time = models.DateTimeField()
    bus_duration = models.IntegerField()
    bus_starting_point = models.CharField(max_length=50)
    bus_destination = models.CharField(max_length=50)

    def __init__(self):
        self.bus_seats_available = self.bus_capacity
    def __str__(self):
        return self.bus_name
    
class Ticket(models.Model):
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