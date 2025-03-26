# Generated by Django 5.1.6 on 2025-03-26 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bus_booking", "0013_remove_booking_journey_booking_bus"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="booking_date",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name="booking",
            name="journey_date",
            field=models.DateField(null=True),
        ),
    ]
