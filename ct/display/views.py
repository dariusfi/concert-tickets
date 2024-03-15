from ct.constants import DELETE_ORDER_DAYS_BEFORE_CONCERT, SENDER_EMAIL
from ct.display.forms import BankStatementForm, CreateOrderForm
from ct.logic.bank_statement import process_bank_statement
from ct.logic.customer import add_to_newsletter
from ct.logic.event import get_event_infos
from ct.logic.invoice import create_invoice_and_tickets
from ct.logic.order import (can_order_be_deleted, create_order, delete_order,
                             is_order_deleted, send_email_invoice_and_tickets)
from ct.logic.payment_reminder import send_payment_reminder
from ct.logic.permissions import is_superuser
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def create_order_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = CreateOrderForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            address_street = form.cleaned_data["address_street"]
            address_number = form.cleaned_data["address_number"]
            address_zip = form.cleaned_data["address_zip"]
            address_city = form.cleaned_data["address_city"]
            address = f"{address_street} {address_number}, {address_zip} {address_city}"

            email = form.cleaned_data["email"]
            event_id = form.cleaned_data["event"]
            number_discount = form.cleaned_data["number_discount"]
            number_regular = form.cleaned_data["number_regular"]
            allows_advertising = form.cleaned_data["allows_advertising"]

            try:
                order = create_order(
                    name, address, email, event_id, number_discount, number_regular
                )
                if allows_advertising:
                    add_to_newsletter(email)
                pdf = create_invoice_and_tickets(order)

                send_email_invoice_and_tickets(order, pdf)
            except Exception as e:
                return render(
                    request,
                    "generic_message.html",
                    {
                        "message": "Bestellung konnte nicht abgeschlossen werden: "
                        + str(e)
                    },
                )

            return render(
                request,
                "generic_message.html",
                {
                    "message": (
                        "Bestellung erfolgreich! Sie erhalten in Kürze eine Bestellbestätigung, sowie die "
                        f"Rechnung und Ihre Tickets per Email. Bitte melden Sie sich bei {SENDER_EMAIL}, "
                        "wenn die Emails nicht innerhalb von 20 Minuten ankommen sollten."
                    )
                },
            )
    else:
        form = CreateOrderForm()

    return render(request, "create_order.html", {"form": form})


def delete_order_view(
    request: HttpRequest, reference_code: str, delete_code: str
) -> HttpResponse:
    if is_order_deleted(reference_code):
        return render(
            request,
            "generic_message.html",
            {"message": "Die Bestellung wurde bereits storniert."},
        )

    if not can_order_be_deleted(reference_code):
        return render(
            request,
            "generic_message.html",
            {
                "message": (
                    f"Eine Bestellung kann nur bis {DELETE_ORDER_DAYS_BEFORE_CONCERT} Tage bzw. "
                    f"{DELETE_ORDER_DAYS_BEFORE_CONCERT * 24} Stunden vor dem Konzertbeginn "
                    "storniert werden."
                )
            },
        )

    if request.method == "GET":
        return render(request, "confirm_delete_order.html")
    else:
        try:
            delete_order(reference_code, delete_code)
            return render(request, "delete_order_success.html")
        except RuntimeError as e:
            return render(request, "generic_message", {"message": str(e)})


def agb(request: HttpRequest) -> HttpResponse:
    return render(request, "agb.html")


@user_passes_test(is_superuser)
def upload_statement(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = BankStatementForm(request.POST, request.FILES)
        if form.is_valid():
            # Read and process the CSV file
            report = process_bank_statement(form.cleaned_data["file"])

            response = HttpResponse(content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = (
                'attachment; filename="übersicht_kartenzahlungen.csv"'
            )
            response.write(report.encode("utf-8"))

            return response
    else:
        form = BankStatementForm()

    return render(request, "upload_bank_statement.html", {"form": form})


def login_view():
    return LoginView.as_view(template_name="login.html")


def logout_view():
    return LogoutView.as_view(
        template_name="generic_message.html",
        extra_context={"message": "Erfolgreich abgemeldet!"},
    )


@user_passes_test(is_superuser)
def dashboard(request: HttpRequest) -> HttpResponse:
    event_infos = get_event_infos()
    return render(request, "dashboard.html", {"event_infos": event_infos})


@user_passes_test(is_superuser)
def payment_reminder(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        send_payment_reminder()

        success_message = (
            "Zahlungserinnerungen werden im Hintergrund versendet. "
            "Es kann ein paar Minuten dauern, bis alle Erinnerungen verschickt wurden."
        )

        return render(
            request,
            "generic_message.html",
            {"message": success_message},
        )

    return render(request, "payment_reminder.html")
