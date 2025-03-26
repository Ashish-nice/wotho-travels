# Generated by Django 5.1.6 on 2025-03-26 06:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bus_booking", "0012_remove_booking_bus_booking_journey"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="booking",
            name="journey",
        ),
        migrations.AddField(
            model_name="booking",
            name="bus",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="bookings",
                to="bus_booking.bus",
            ),
        ),
    ]
