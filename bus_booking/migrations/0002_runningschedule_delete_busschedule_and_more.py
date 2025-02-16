# Generated by Django 5.1.6 on 2025-02-16 17:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bus_booking", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="RunningSchedule",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("city", models.CharField(max_length=50)),
                ("arrival_time", models.TimeField(blank=True, null=True)),
                ("departure_time", models.TimeField()),
                (
                    "running_day",
                    models.CharField(
                        choices=[
                            ("Monday", "Monday"),
                            ("Tuesday", "Tuesday"),
                            ("Wednesday", "Wednesday"),
                            ("Thursday", "Thursday"),
                            ("Friday", "Friday"),
                            ("Saturday", "Saturday"),
                            ("Sunday", "Sunday"),
                        ],
                        max_length=10,
                    ),
                ),
                ("stop_number", models.PositiveIntegerField()),
                (
                    "bus",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="schedules",
                        to="bus_booking.bus",
                    ),
                ),
            ],
            options={
                "ordering": ["bus", "running_day", "stop_number"],
            },
        ),
        migrations.DeleteModel(
            name="BusSchedule",
        ),
        migrations.AddConstraint(
            model_name="runningschedule",
            constraint=models.UniqueConstraint(
                fields=("bus", "city", "day"), name="unique_bus_city_day"
            ),
        ),
    ]
