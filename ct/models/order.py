from django.db import models
from ct.logic.shared import datetime_as_german_date_str

from ct.models.event import Event


class Order(models.Model):
    reference_code = models.CharField(max_length=50, primary_key=True)
    order_date = models.DateTimeField()
    name = models.CharField(max_length=254)
    address = models.CharField(max_length=500)
    email = models.EmailField(max_length=254)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    number_discount = models.PositiveIntegerField(default=0)
    number_regular = models.PositiveIntegerField(default=0)
    delete_code = models.CharField(max_length=20)
    is_deleted = models.BooleanField(default=False)
    delete_date = models.DateTimeField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateTimeField(null=True, blank=True)
    reminder_sent = models.BooleanField(default=False)
    reminder_date = models.DateTimeField(null=True, blank=True)
    warning_sent = models.BooleanField(default=False)
    warning_date = models.DateTimeField(null=True, blank=True)
    is_refunded = models.BooleanField(default=False)
    refund_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.reference_code

    @property
    def order_date_german_tz_str(self) -> str:
        return datetime_as_german_date_str(self.order_date)
