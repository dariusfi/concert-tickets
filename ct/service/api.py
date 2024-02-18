from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import BasicAuthentication
from ct.models.event import Event

from ct.models.ticket import Ticket

class Events(APIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = Event.objects.filter(is_active=True)
        event_tuples = [(e.key, str(e)) for e in events]
        return Response(event_tuples)
    

class Tickets(APIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id, *args, **kwargs):
        event = get_object_or_404(Event, key=event_id)
        tickets = Ticket.objects.filter(order__event=event)

        ticket_data = [
            {
                "ticket_code": ticket.ticket_code,
                "type": ticket.type,
                "is_paid": ticket.order.is_paid,
                "is_order_deleted": ticket.order.is_deleted
            }
            for ticket in tickets
        ]

        return Response(ticket_data)