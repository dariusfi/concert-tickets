import threading
from datetime import timedelta

from django.utils import timezone

from ct.constants import (
    BANK_TRANSFER_TIME_DAYS,
    EMAIL_CLOSING,
    IBAN,
    NAME_ORCHESTRA,
    NAME_ORCHESTRA_FULL,
    PAYMENT_GRACE_PERIOD_DAYS,
    SENDER_EMAIL,
    WARNING_GRACE_PERIOD_DAYS,
)
from ct.logic.order import calculate_ticket_price
from ct.logic.shared import datetime_as_german_date_str, send_email
from ct.models.order import Order


def send_payment_reminder():
    send_first_reminders()
    send_first_warnings()


def send_first_reminders():
    # Calculate the cutoff date before which orders should be paid by now. We add additional days to the grace
    # period to account for transfer time
    before_grace_period_first_reminder = timezone.now() - timedelta(
        days=PAYMENT_GRACE_PERIOD_DAYS + BANK_TRANSFER_TIME_DAYS
    )

    # Query for orders who need to be reminded
    first_reminder_orders = list(
        Order.objects.filter(
            order_date__lte=before_grace_period_first_reminder,
            is_paid=False,
            is_deleted=False,
            reminder_sent=False,
            warning_sent=False,  # This should not occur if reminder_sent is False
        )
    )
    background_thread = threading.Thread(
        target=send_first_reminder_emails(first_reminder_orders)
    )
    background_thread.start()


def send_first_reminder_emails(unpaid_orders: list[Order]):
    for order in unpaid_orders:
        subject = f"Zahlungserinnerung {NAME_ORCHESTRA} {order.reference_code}"

        num_tickets = order.number_discount + order.number_regular
        body = f"""
Liebe*r {order.name},

nochmals herzlichen Dank für Ihre Bestellung vom {order.order_date_german_tz_str} (Rechnungsnummer {order.reference_code}) bei der {NAME_ORCHESTRA}! Sie haben {f"{num_tickets} Tickets" if num_tickets > 1 else "ein Ticket"} für das Konzert "{order.event}" bestellt.
Leider ist bisher noch keine Zahlung für diese Bestellung bei uns eingegangen. Falls Sie die Zahlungen bereits getätigt haben, brauchen Sie nichts weiter zu unternehmen. Falls Sie die Zahlung vergessen haben – kein Problem! Überweisen Sie diese bitte schnellstmöglich auf folgendes Konto:

Betrag: {calculate_ticket_price(order)} €
Name: {NAME_ORCHESTRA_FULL}
IBAN: {IBAN}
Verwendungszweck: Karten {order.reference_code}

Mit musikalischen Grüßen,
{EMAIL_CLOSING}
"""

        send_email(
            subject=subject, body=body, recipients=[order.email], bcc_email=SENDER_EMAIL
        )

        order.reminder_sent = True
        order.reminder_date = timezone.now()
        order.save()


def send_first_warnings():
    before_grace_period_first_warning = timezone.now() - timedelta(
        days=WARNING_GRACE_PERIOD_DAYS + BANK_TRANSFER_TIME_DAYS
    )

    first_warning_orders = list(
        Order.objects.filter(
            is_paid=False,
            is_deleted=False,
            reminder_sent=True,
            reminder_date__lte=before_grace_period_first_warning,
            warning_sent=False,
        )
    )
    background_thread = threading.Thread(
        target=send_first_warning_emails(first_warning_orders)
    )
    background_thread.start()


def send_first_warning_emails(unpaid_orders: list[Order]):
    for order in unpaid_orders:
        subject = f"Mahnung {NAME_ORCHESTRA} {order.reference_code}"

        num_tickets = order.number_discount + order.number_regular
        body = f"""
Liebe*r {order.name},

Sie haben am {order.order_date_german_tz_str} (Rechnungsnummer {order.reference_code}) bei uns {f"{num_tickets} Tickets" if num_tickets > 1 else "ein Ticket"} für das Konzert "{order.event}" bestellt.

Leider ist bisher immer noch keine Zahlung für diese Bestellung bei uns eingegangen. Wir haben Ihnen bereits eine Zahlungserinnerung am {datetime_as_german_date_str(order.reminder_date)} per Email geschickt. Falls Sie die Zahlungen in der Zwischenzeit getätigt haben, brauchen Sie nichts weiter zu unternehmen. Falls Sie noch nicht gezahlt haben, holen Sie dies bitte schnellstmöglich nach. Ansonsten müssen wir Ihnen leider eine postalische Mahnung zzgl. Verzugszinsen und einer Bearbeitungsgebühr zukommen zu lassen.

Betrag: {calculate_ticket_price(order)} €
Name: {NAME_ORCHESTRA_FULL}
IBAN: {IBAN}
Verwendungszweck: Karten {order.reference_code}

Mit freundlichen Grüßen,
{EMAIL_CLOSING}
"""

        send_email(
            subject=subject, body=body, recipients=[order.email], bcc_email=SENDER_EMAIL
        )

        order.warning_sent = True
        order.warning_date = timezone.now()
        order.save()
