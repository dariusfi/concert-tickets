import os

TICKET_PRICE_DISCOUNT = os.getenv("TICKET_PRICE_DISCOUNT", 8)
TICKET_PRICE_REGULAR = os.getenv("TICKET_PRICE_REGULAR", 20)

# The number of days before a concert until when an order can be deleted
DELETE_ORDER_DAYS_BEFORE_CONCERT = 5

TICKET_SALE_CLOSE_BEFORE_CONCERT_HOURS = 3

BANK_TRANSFER_TIME_DAYS = 2
PAYMENT_GRACE_PERIOD_DAYS = 14
WARNING_GRACE_PERIOD_DAYS = 7

NAME_ORCHESTRA = "Fantasie Philharmonie"
NAME_ORCHESTRA_FULL = NAME_ORCHESTRA + " e.V."

EMAIL_SERVER = "smtp.your-email-server"
EMAIL_PORT = 587
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SENDER_EMAIL = "tickets@your-orchestra.de"

IBAN = "DE00 0000 0000 0000 0000"
BIC = "YOURBIC"

HEADER_INVOICE = [
    NAME_ORCHESTRA_FULL,
    "Johann S. Bach",
    "Bachweg 5",
    "12345 Eisenach",
    "Mobil: XXXX XXXXXX",
    f"Mail: {SENDER_EMAIL}",
    "https://your-website.de",
]

FOOTER_INVOICE = [
    NAME_ORCHESTRA_FULL,
    "Eingetragen im Vereinsregister ...",
    "Bankverbindung: ",
    f"IBAN: {IBAN}, BIC: {BIC}",
    "Steuernummer: ..., Finanzamt ...",
]

BASE_URL = "https://tickets.your-orchestra.de"

EMAIL_CLOSING = f"""Johann S. Bach
i.A. {NAME_ORCHESTRA}
"""
