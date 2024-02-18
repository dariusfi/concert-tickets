import uuid
from datetime import datetime, timedelta
from io import BytesIO

from django.utils import timezone

from ct.constants import (
    BASE_URL,
    DELETE_ORDER_DAYS_BEFORE_CONCERT,
    EMAIL_CLOSING,
    IBAN,
    NAME_ORCHESTRA,
    NAME_ORCHESTRA_FULL,
    PAYMENT_GRACE_PERIOD_DAYS,
    SENDER_EMAIL,
    TICKET_PRICE_DISCOUNT,
    TICKET_PRICE_REGULAR,
    TICKET_SALE_CLOSE_BEFORE_CONCERT_HOURS,
)
from ct.logic.event import get_remaining_tickets
from ct.logic.shared import datetime_as_german_date_str, send_email
from ct.models.event import Event
from ct.models.order import Order


def create_order(
    name: str,
    address: str,
    email: str,
    event_id: str,
    number_discount: int,
    number_regular: int,
) -> Order:
    reference_code = generate_random_reference_code()
    delete_code = generate_random_delete_code()
    event = Event.objects.get(key=event_id)

    if event.datetime - timezone.now() <= timedelta(
        hours=TICKET_SALE_CLOSE_BEFORE_CONCERT_HOURS
    ):
        raise RuntimeError(
            f"Eine Bestellung über den Onlineshop ist nur bis {TICKET_SALE_CLOSE_BEFORE_CONCERT_HOURS} Stunden "
            "vor Konzertbeginn möglich. Bitte versuchen Sie es über die Abendkasse."
        )

    remaining_tickets = get_remaining_tickets(event_id)

    if remaining_tickets < number_discount + number_regular:
        raise RuntimeError(
            f"Es sind nur noch {remaining_tickets} Tickets für dieses Konzert verfügbar."
        )

    new_order = Order(
        name=name,
        order_date=timezone.now(),
        address=address,
        reference_code=reference_code,
        email=email,
        event=event,
        number_discount=number_discount,
        number_regular=number_regular,
        delete_code=delete_code,
    )
    new_order.save()

    return new_order


def generate_random_reference_code() -> str:
    """
    Generates a 8-digit, hexadecimal "reference code", which is used for order payments.
    Codes including "O"s and Zeros are skipped, as they are easily mixed up.

    :return: The reference code as string
    """
    while True:
        code = uuid.uuid4().hex[:8].upper()
        if "O" not in code and "0" not in code:
            if not Order.objects.filter(reference_code=code).exists():
                return code


def generate_random_delete_code() -> str:
    return uuid.uuid4().hex[:20]


def can_order_be_deleted(reference_code: str) -> bool:
    order = Order.objects.get(pk=reference_code)
    now_date = timezone.now()
    return (order.event.datetime - now_date) >= timedelta(
        days=DELETE_ORDER_DAYS_BEFORE_CONCERT
    )


def is_order_deleted(reference_code: str) -> bool:
    order = Order.objects.get(pk=reference_code)
    return order.is_deleted


def delete_order(reference_code: str, delete_code: str):
    order = Order.objects.get(pk=reference_code)

    if order.delete_code != delete_code:
        raise RuntimeError(
            f"Link zum Löschen der Bestellung ungültig. Bitte kontaktieren Sie {SENDER_EMAIL}."
        )

    order.is_deleted = True
    order.delete_date = datetime.utcnow()
    order.save()

    # Send email confirmation
    subject = f"{NAME_ORCHESTRA} - Stornierungsbestätigung {order.reference_code}"

    if order.is_paid:
        text_payment = (
            "Ihre Zahlung ist bereits eingegangen und wird Ihnen zurückerstattet."
        )
    else:
        text_payment = "Falls Sie die Rechnung bereits gezahlt haben, wird Ihnen der Betrag zurückerstattet."

    body = f"""
Liebe*r {order.name},

Ihre Bestellung mit der Rechnungsnummer {order.reference_code} (Konzert {order.event.location}) wurde erfolgreich storniert. {text_payment}

Mit musikalischen Grüßen,
{EMAIL_CLOSING}
    """
    send_email(
        subject=subject, body=body, recipients=[order.email], bcc_email=SENDER_EMAIL
    )


# Calculate the total ticket price for an order
def calculate_ticket_price(order) -> int:
    total_amount = (
        order.number_discount * TICKET_PRICE_DISCOUNT
        + order.number_regular * TICKET_PRICE_REGULAR
    )

    return total_amount


def send_email_invoice_and_tickets(order: Order, pdf_buffer: BytesIO) -> None:
    email_subject = f"{NAME_ORCHESTRA} - Rechnung und Tickets {order.reference_code}"

    total_ticket_price = calculate_ticket_price(order)
    num_tickets = order.number_discount + order.number_regular
    email_body = f"""
Liebe*r {order.name},

herzlichen Dank für Ihre Bestellung von {f"{num_tickets} Tickets" if num_tickets > 1 else "einem Ticket"} für das Konzert am {datetime_as_german_date_str(order.event.datetime)} bei der {NAME_ORCHESTRA}! Anbei finden Sie die Rechnung und {"Ihre Tickets" if num_tickets > 1 else "Ihr Ticket"} als PDF-Datei. Sie können {"die Tickets" if num_tickets > 1 else "das Ticket"} entweder ausdrucken oder auf Ihrem Smartphone vorzeigen. 

Bitte überweisen Sie den Gesamtbetrag von {total_ticket_price} € innerhalb der nächsten {PAYMENT_GRACE_PERIOD_DAYS} Tage auf folgendes Konto:

Name: {NAME_ORCHESTRA_FULL}
IBAN: {IBAN}
Verwendungszweck: Karten {order.reference_code}

Wir freuen uns auf Ihren Besuch!
{EMAIL_CLOSING}

====================
Um Ihre Bestellung zu stornieren, klicken Sie auf den folgenden Link:
{BASE_URL}/delete_order/{order.reference_code}/{order.delete_code}
Bitte beachten Sie, dass eine Bestellung nur bis {DELETE_ORDER_DAYS_BEFORE_CONCERT} Tage vor dem Konzert storniert werden kann (gerechnet in {DELETE_ORDER_DAYS_BEFORE_CONCERT * 24} Stunden vor Konzertbeginn). Falls Sie ihre Bestellung ändern wollen, stornieren Sie diese bitte ebenfalls und geben Sie eine neue Bestellung auf. Bereits bezahlte Beträge werden Ihnen nach der Stornierung erstattet.

Beim Ausfüllen des Bestellformulars haben Sie unserer AGB zugestimmt: {BASE_URL}/agb
"""

    attachment_filename = f"{order.order_date_german_tz_str} Rechnung_Tickets_ct.pdf"

    send_email(
        subject=email_subject,
        body=email_body,
        recipients=[order.email],
        bcc_email=SENDER_EMAIL,
        pdf_attachment_content=pdf_buffer,
        attachment_name=attachment_filename,
    )
