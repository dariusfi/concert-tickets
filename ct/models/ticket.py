from enum import Enum
from django.db import models
from ct.constants import TICKET_PRICE_DISCOUNT, TICKET_PRICE_REGULAR

from ct.models.order import Order


class TicketType(Enum):
    REGULAR = "Vollpreis"
    DISCOUNT = "Ermäßigt"

class Ticket(models.Model):
    ticket_code = models.CharField(max_length=36, primary_key=True)
    type = models.CharField(
        max_length=30, choices=[(t.name, t.value) for t in TicketType]
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    def __str__(self):
        return self.ticket_code

    @property
    def price(self):
        return TICKET_PRICE_REGULAR if self.type == TicketType.REGULAR else TICKET_PRICE_DISCOUNT

    @property
    def display_type(self):
        return TicketType[self.type].value