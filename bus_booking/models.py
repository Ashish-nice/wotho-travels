from django.db import models
from users.models import Profile
from django.contrib.postgres.fields import ArrayField
# Create your models here.
class Bus(models.Model):
    bus_id = models.AutoField(primary_key=True)
    bus_name = models.CharField(max_length=50)
    bus_number = models.CharField(max_length=50)
    bus_capacity = models.IntegerField()
    bus_seats_available = ArrayField(models.IntegerField(),default=list)
    base_fare = models.IntegerField(null=True,blank=True)
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
        if not self.pk:
            self.bus_seats_available = [self.bus_capacity]*(len(self.bus_route)-1)
            super().save(*args, **kwargs)

class BusFare(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    from_city = models.CharField(max_length=50)
    to_city = models.CharField(max_length=50)
    fare = models.DecimalField(max_digits=10, decimal_places=2)  # Stores fare amount
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
        fare_obj = BusFare.objects.get(bus=bus, from_city=from_city, to_city=to_city, seat_type=seat_type, conditioning=conditioning)
        if fare_obj.fare:
            fare = fare_obj.fare
            return fare
        else:
            fare_obj.save()


class Booking(models.Model):
    ticket_id = models.AutoField(primary_key=True)
    ticket_user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    ticket_bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    from_city = models.CharField(max_length=50,null=True,blank=True)
    to_city = models.CharField(max_length=50,null=True,blank=True)
    fare = models.IntegerField(null=True,blank=True)
    ticket_seats = models.IntegerField()
    ticket_time = models.DateTimeField()
    ticket_status = models.CharField(max_length=50)

    def __str__(self):
        return self.ticket_id
