# Generated by Django 5.1.6 on 2025-03-25 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bus_booking", "0006_booking_otp_booking_otp_created_at_ticket"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="booking_payment",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="ticket",
            name="ticket_payment",
            field=models.BooleanField(default=False),
        ),
    ]
