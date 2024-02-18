import csv
from datetime import datetime
from io import TextIOWrapper

from ct.logic.order import calculate_ticket_price
from ct.models.order import Order


def process_bank_statement(file) -> str:
    file_wrapper = TextIOWrapper(file.file, encoding="utf-8")
    reader = csv.DictReader(file_wrapper, delimiter=";")

    payments_per_reference_code = calculate_payments_per_reference_code(reader)
    return generate_payments_report(payments_per_reference_code)


def calculate_payments_per_reference_code(reader):
    # We first create a dictionary of reference_codes:payment_details, as that will help with
    # dealing with refunded tickets and payments paid in multiple installments (e.g.
    # if user sent wrong amount at first).
    payments = {}

    for row in reader:
        date = datetime.strptime(row["Buchungstag"], r"%d.%m.%Y")
        reference_text = row["Verwendungszweck"]
        amount = float(row["Betrag"].replace(",", "."))

        # The reference text should start with "Karten XXXXXXXX" or "Stornierung Karten XXXXXXXX",
        # with XXXXXXXX being the reference code.
        if " " in reference_text:
            parts = reference_text.strip().split(" ")
            if parts[0] == "Stornierung":
                reference_code = parts[2]
            else:
                reference_code = parts[1]
        else:
            reference_code = reference_text.strip()[-8:].strip()

        if reference_code in payments:
            # This reference_code already occured before in the account statement
            # Load what we already stored from the previous rows
            current_balance = payments[reference_code]["balance"]
            current_payment_date = payments[reference_code]["payment_date"]
            current_refund_date = payments[reference_code]["refund_date"]

            # Update the balance and the dates where applicable
            payments[reference_code] = {
                "balance": current_balance + amount,
                "payment_date": date if amount > 0 else current_payment_date,
                "refund_date": date if amount < 0 else current_refund_date,
            }
        else:
            # This is the first row for this reference_code
            payments[reference_code] = {
                "balance": amount,
                "payment_date": date if amount > 0 else None,
                "refund_date": date if amount < 0 else None,
            }

    return payments


def generate_payments_report(payment_details) -> str:
    # Create a csv report with information on all payments in the bank statement
    report = "Fehlertyp;Verwendungstext;Beschreibung\n"

    # Now that we calculated the details for each order, compare that with the order properties to
    # determine which orders are succesfully paid, wrongly paid, or need to be refunded.
    for reference_code, payment_details in payment_details.items():
        try:
            order = Order.objects.get(pk=reference_code)

            if payment_details["balance"] == 0.0:
                report = handle_zero_balance(
                    reference_code, order, payment_details, report
                )
            elif payment_details["balance"] > 0.0:
                report = handle_positive_balance(
                    reference_code, order, payment_details, report
                )
            else:
                report += (
                    f"FALSCHE_ERSTATTUNG;{reference_code};Bestellung {reference_code} wurde inkorrekt erstattet. "
                    f"Überwiesener Betrag minus erstatteter Betrag ist {payment_details['balance']}. Bitte überprüfen.\n"
                )

            order.save()

        except Order.DoesNotExist:
            report += (
                f"NICHT_ZUORDENBAR;{reference_code};Buchungsnummer '{reference_code}' "
                "konnte keiner Bestellung zugeordnet werden.\n"
            )

    return report


def handle_zero_balance(reference_code, order, payment_details, report) -> str:
    if not order.is_paid:
        # If the balance is 0, there had to be a payment already, as you cannot transfer 0 €
        order.is_paid = True
        order.payment_date = payment_details["payment_date"]

    if order.is_deleted:
        if not order.is_refunded:
            report += f"ERFOLGREICHE_ERSTATTUNG;{reference_code};Bestellung {reference_code} wurde erstattet.\n"
            order.is_refunded = True
            order.refund_date = payment_details["refund_date"]
    else:
        report += (
            f"FALSCHE_ERSTATTUNG;{reference_code};Bestellung {reference_code} "
            "wurde fälschlicherweise erstattet. Die Bestellung wurde nicht durch den "
            "Kunden storniert.\n"
        )
    return report


def handle_positive_balance(reference_code, order, payment_details, report) -> str:
    if order.is_deleted:
        report += (
            f"ERSTATTUNG_NOTWENDIG;{reference_code};Für Bestellung {reference_code} müssen "
            f"{payment_details['balance']} € erstattet werden.\n"
        )
    else:
        outstanding = calculate_ticket_price(order)
        if outstanding != payment_details["balance"]:
            report += (
                f"FALSCHER_BETRAG;{reference_code};Bestellung {reference_code} "
                f"wurde inkorrekt bezahlt. Sollte sein: {outstanding} €. Tatsächlich bezahlt: "
                f"{payment_details['balance']} €.\n"
            )
            # This should not be stored as paid yet. Just to be sure, we overwrite the values.
            order.is_paid = False
            order.payment_date = None
        else:
            report += (
                f"BEZAHLT;{reference_code};Bestellung {reference_code} wurde bezahlt.\n"
            )
            order.is_paid = True
            order.payment_date = payment_details["payment_date"]

    return report
