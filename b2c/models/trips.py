"""B2C Trip Planning Models - Placeholder"""
from django.db import models
from .customer import Customer

class Trip(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'b2c_trip'

class TripDay(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    day_number = models.IntegerField()
    date = models.DateField()
    class Meta:
        db_table = 'b2c_trip_day'

class TripActivity(models.Model):
    trip_day = models.ForeignKey(TripDay, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    start_time = models.TimeField()
    class Meta:
        db_table = 'b2c_trip_activity'
