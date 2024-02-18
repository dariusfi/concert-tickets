from django.db import models
import pytz


class Event(models.Model):
    key = models.CharField(max_length=30, primary_key=True)
    location = models.CharField(max_length=100)
    datetime = models.DateTimeField()
    program = models.CharField(max_length=500)
    conductor = models.CharField(max_length=50)
    max_number_tickets = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        time_in_berlin_tz = self.datetime.astimezone(pytz.timezone('Europe/Berlin')).strftime(r'%d.%m.%Y, %H:%M')
        return f"{time_in_berlin_tz} Uhr, {self.location}"
