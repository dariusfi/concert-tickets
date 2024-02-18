import json
import uuid
from datetime import timedelta
from pathlib import Path

import pytz
from reportlab.graphics.barcode.qr import QrCode, QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Flowable, Paragraph
from reportlab.platypus.flowables import Flowable

from ct.logic.styles import STYLE_NORMAL, STYLE_NORMAL_BOLD, STYLE_SMALL
from ct.models.ticket import Ticket, TicketType


# Create a new ticket object for a given order
def create_ticket(order, type: TicketType):
    if type not in TicketType:
        raise RuntimeError("Invalid ticket type")

    ticket_code = generate_random_ticket_code(order)
    ticket = Ticket(ticket_code=ticket_code, order=order, type=type.name)
    ticket.save()
    return ticket


def generate_random_ticket_code(order):
    while True:
        # Generate a uuid
        ticket_code = str(uuid.uuid4())
        if not Ticket.objects.filter(ticket_code=ticket_code).exists():
            return ticket_code


def insert_image(canvas, image_path, x, y, width=None, height=None):
    img = ImageReader(image_path)
    img_width, img_height = img.getSize()

    if width is None and height is not None:
        width = (height / img_height) * img_width
    elif height is None and width is not None:
        height = (width / img_width) * img_height

    canvas.drawImage(img, x, y, width, height)


class TicketFlowable(Flowable):
    def __init__(self, order, width, ticket):
        Flowable.__init__(self)
        self.width = width
        self.height = 250
        self.PADDING = 20
        self.ticket = ticket
        self.order = order

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        # Set up the drawing context
        c = self.canv
        c.saveState()

        # Draw the outer box with a border
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.rect(0, 0, self.width, self.height)

        # Draw logos on the left side of the ticket
        ORCHESTRA_LOGO_WIDTH = 160
        insert_image(
            c,
            Path(__file__).parent.parent / "static" / "ct" / "logo.png",
            x=self.width / 4 - ORCHESTRA_LOGO_WIDTH / 2,
            y=105,
            width=ORCHESTRA_LOGO_WIDTH,
        )

        SPONSOR1_LOGO_WIDTH = 90
        insert_image(
            c,
            Path(__file__).parent.parent / "static" / "ct" / "sponsor1.jpg",
            x=self.width / 4 - SPONSOR1_LOGO_WIDTH / 2,
            y=55,
            width=SPONSOR1_LOGO_WIDTH,
        )

        SPONSOR2_LOGO_WIDTH = 80
        insert_image(
            c,
            Path(__file__).parent.parent / "static" / "ct" / "sponsor2.png",
            x=self.width / 4 - SPONSOR2_LOGO_WIDTH / 2,
            y=15,
            width=SPONSOR2_LOGO_WIDTH,
        )

        # Create paragraphs on the left
        p1 = Paragraph(
            "<br/>".join(json.loads(self.order.event.program)), STYLE_NORMAL_BOLD
        )
        p1.wrap(250, self.height)
        p1.drawOn(c, self.width / 2, self.height - 45)
        p2 = Paragraph(f"Dirigent: {self.order.event.conductor}", STYLE_NORMAL)
        p2.wrap(250, self.height)
        p2.drawOn(c, self.width / 2, self.height - 65)

        # Generate and draw the QR code on the right
        qr_code = QrCode(self.ticket.ticket_code, height=100, width=100)
        qr_code.drawOn(c, self.width / 2 + 50, 80)

        # Calculate weekday from event date
        # Set locale to Germany so that the weekday is returned in German
        weekday = self.order.event.datetime.astimezone(
            pytz.timezone("Europe/Berlin")
        ).strftime("%A")

        # English to German weekday translation dictionary
        weekday_translation = {
            "Monday": "Montag",
            "Tuesday": "Dienstag",
            "Wednesday": "Mittwoch",
            "Thursday": "Donnerstag",
            "Friday": "Freitag",
            "Saturday": "Samstag",
            "Sunday": "Sonntag",
        }
        localized_event_time = self.order.event.datetime.astimezone(
            pytz.timezone("Europe/Berlin")
        )
        p3 = Paragraph(
            f"{weekday_translation[weekday]}, den {localized_event_time.strftime(r'%d.%m.%Y')} "
            f"um {localized_event_time.strftime(r'%H:%M')} Uhr",
            STYLE_NORMAL,
        )
        p3.wrap(250, self.height)
        p3.drawOn(c, self.width / 2, 60)

        p4 = Paragraph(self.order.event.location, STYLE_NORMAL_BOLD)
        p4.wrap(250, self.height)
        p4.drawOn(c, self.width / 2, 45)

        entrance_time = (
            (self.order.event.datetime - timedelta(minutes=30))
            .astimezone(pytz.timezone("Europe/Berlin"))
            .strftime(r"%H:%M")
        )
        p5 = Paragraph(
            f"{self.ticket.display_type}, Freie Platzwahl, Einlass ab {entrance_time} Uhr",
            STYLE_SMALL,
        )
        p5.wrap(140, self.height)
        p5.drawOn(c, self.width / 2, 15)

        # Restore the drawing context
        c.restoreState()


def create_qr_code_drawing(reference_code):
    qr_code = QrCodeWidget(reference_code)
    bounds = qr_code.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    drawing = Drawing(
        3.5 * cm, 3.5 * cm, transform=[3.5 * cm / width, 0, 0, 3.5 * cm / height, 0, 0]
    )
    drawing.add(qr_code)

    return drawing
