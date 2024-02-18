from django.contrib import admin

from ct.models.event import Event
from ct.models.customer import Customer
from ct.models.order import Order
from ct.models.ticket import Ticket


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "reference_code",
        "order_date",
        "email",
        "event",
        "number_discount",
        "number_regular",
        "is_paid",
        "is_deleted",
        "is_refunded",
        "reminder_sent",
        "warning_sent",
    ]


admin.site.register(Order, OrderAdmin)


class CustomerAdmin(admin.ModelAdmin):
    list_display = ["email", "allows_advertising"]


admin.site.register(Customer, CustomerAdmin)


class TicketAdmin(admin.ModelAdmin):
    list_display = ["ticket_code", "type", "order"]

admin.site.register(Ticket, TicketAdmin)


class EventAdmin(admin.ModelAdmin):
    list_display = ["key", "location", "datetime"]


admin.site.register(Event, EventAdmin)
