from ct.models.event import Event
from ct.models.ticket import Ticket, TicketType


def get_remaining_tickets(event_id: str) -> int:
    event = Event.objects.get(pk=event_id)
    num_tickets_sold = Ticket.objects.filter(
        order__event=event, order__is_deleted=False
    ).count()
    return max(event.max_number_tickets - num_tickets_sold, 0)


def get_event_infos():
    events = Event.objects.filter(is_active=True)
    event_infos = []
    for event in events:
        all_tickets = Ticket.objects.filter(order__event=event)
        num_discount_tickets = all_tickets.filter(type=TicketType.DISCOUNT.name, order__is_deleted=False).count()
        num_regular_tickets = all_tickets.filter(type=TicketType.REGULAR.name, order__is_deleted=False).count()

        num_discount_deleted = all_tickets.filter(type=TicketType.DISCOUNT.name, order__is_deleted=True).count()
        num_regular_deleted = all_tickets.filter(type=TicketType.REGULAR.name, order__is_deleted=True).count()

        event_infos.append(
            {
                "name": str(event),
                "max_number_tickets": event.max_number_tickets,
                "regular_sold": num_regular_tickets,
                "discount_sold": num_discount_tickets,
                "regular_deleted": num_regular_deleted,
                "discount_deleted":num_discount_deleted,
                "total_sold": num_regular_tickets + num_discount_tickets,
                "remaining_tickets": get_remaining_tickets(event.key),
            }
        )
    return event_infos
