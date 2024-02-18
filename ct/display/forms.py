from django import forms
from django.utils.safestring import mark_safe
from ct.constants import TICKET_PRICE_DISCOUNT, TICKET_PRICE_REGULAR
from ct.logic.event import get_remaining_tickets

from ct.models.event import Event


class CreateOrderForm(forms.Form):
    name = forms.CharField(max_length=254, label="Vorname Nachname")
    address_street = forms.CharField(max_length=254, label="Straße")
    address_number = forms.CharField(max_length=30, label="Hausnummer")
    address_zip = forms.IntegerField(label="PLZ")
    address_city = forms.CharField(max_length=254, label="Stadt")

    email = forms.EmailField(max_length=254, label="E-Mail")
    event = forms.ChoiceField(label="Veranstaltung")
    number_discount = forms.IntegerField(initial=0, label=f"Anzahl Ermäßigt ({TICKET_PRICE_DISCOUNT} €) - Menschen mit Behinderung, Kinder, Schüler:innen, Studierende und Auszubildende)")
    number_regular = forms.IntegerField(initial=0, label=f"Anzahl Normalpreis ({TICKET_PRICE_REGULAR} €)")
    allows_advertising = forms.BooleanField(
        initial=False,
        label="Ich würde gerne über zukünftige Konzerte per E-Mail informiert werden (optional).",
        required=False,
    )
    accept_agb = forms.BooleanField(
        initial=False,
        required=True,
        label=mark_safe("Ich stimme den <a href='agb' target='_blank'>AGB</a> zu."),
    )

    def __init__(self, *args, **kwargs):
        super(CreateOrderForm, self).__init__(*args, **kwargs)

        # Display all active events
        events = Event.objects.filter(is_active=True)

        # Add count of remaining tickets to event choice label
        self.fields["event"].choices = [
            (e.key, f"{e} ({get_remaining_tickets(e.key)} Plätze verfügbar)") for e in events
        ]

    def clean(self):
        cleaned_data = super().clean()
        total_tickets = cleaned_data.get('number_discount') + cleaned_data.get('number_regular')

        if total_tickets == 0:
            raise forms.ValidationError("Bitte wählen Sie mindestens ein Ticket aus.")

class BankStatementForm(forms.Form):
    file = forms.FileField(label="Wähle CSV aus")
