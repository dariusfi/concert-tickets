from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    FrameBreak,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
)
from reportlab.platypus.flowables import Flowable, HRFlowable

from ct.constants import (FOOTER_INVOICE, HEADER_INVOICE, IBAN,
                           NAME_ORCHESTRA_FULL, PAYMENT_GRACE_PERIOD_DAYS,
                           TICKET_PRICE_DISCOUNT, TICKET_PRICE_REGULAR)
from ct.logic.order import calculate_ticket_price
from ct.logic.styles import (STYLE_HEADING, STYLE_IMPORTANT, STYLE_NORMAL,
                              STYLE_SMALL, STYLE_SMALL_CENTERED)
from ct.logic.ticket import TicketFlowable, create_ticket
from ct.models.order import Order
from ct.models.ticket import TicketType

HEADER_HEIGHT = 110
FOOTER_HEIGHT = 80
FRAME_SPACE = 12


class PositionedImage(Flowable):
    def __init__(self, image_path, x, y, width, height, hAlign="LEFT"):
        Flowable.__init__(self)
        self.image_path = image_path
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.hAlign = hAlign

    def draw(self):
        self.canv.drawImage(
            self.image_path, self.x, self.y, width=self.width, height=self.height
        )


# Create a PDF for a single order
def create_invoice_and_tickets(order: Order) -> BytesIO:
    pdf_buffer = BytesIO()

    doc = BaseDocTemplate(pdf_buffer, pagesize=A4, showBoundary=0)

    setup_page_templates(doc)

    story = []

    generate_invoice_page(story, order)

    story.append(NextPageTemplate("tickets"))
    story.append(PageBreak())

    generate_ticket_page(doc, story, order)

    doc.build(story)
    pdf_buffer.seek(0)  # Reset buffer position to the beginning
    return pdf_buffer


def setup_page_templates(doc: BaseDocTemplate):
    # Define a two-column header layout
    header_left = Frame(
        doc.leftMargin,
        A4[1] - doc.topMargin - HEADER_HEIGHT,
        doc.width / 2 - FRAME_SPACE / 2 + 30,
        HEADER_HEIGHT,
        id="header_left",
    )

    header_right = Frame(
        doc.leftMargin + doc.width / 2 + 6 + 30,
        A4[1] - doc.topMargin - HEADER_HEIGHT,
        doc.width / 2 - FRAME_SPACE / 2 - 30,
        HEADER_HEIGHT,
        id="header_right",
    )

    main_content = Frame(
        doc.leftMargin,
        doc.bottomMargin + FOOTER_HEIGHT,
        doc.width,
        doc.height - HEADER_HEIGHT - 2 * FRAME_SPACE - FOOTER_HEIGHT,
        id="main_content",
    )

    footer = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        FOOTER_HEIGHT,
        id="footer",
    )

    full_page = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="full",
    )

    full_page_template = PageTemplate(id="tickets", frames=[full_page])

    invoice_template = PageTemplate(
        id="invoice", frames=[header_left, header_right, main_content, footer]
    )

    doc.addPageTemplates([invoice_template, full_page_template])


def generate_invoice_page(story, order):
    add_to_story(story, HEADER_INVOICE, STYLE_SMALL)

    logo = PositionedImage(
        Path(__file__).parent.parent / "static" / "ct" / "logo.png",
        x=-20,
        y=0,
        width=129,
        height=95,
        hAlign="RIGHT",
    )
    story.append(logo)

    add_to_story(story, "Rechnung", STYLE_HEADING)
    add_to_story(
        story,
        [
            f"Datum: {order.order_date_german_tz_str}",
            f"Empfänger: {order.name}, {order.address}",
            f"Rechnungsnummer: {order.reference_code}",
        ],
    )

    add_space(story)

    add_to_story(
        story,
        [
            f"Leistung: Semesterkonzert der {NAME_ORCHESTRA_FULL}",
            str(order.event),
        ],
    )

    add_space(story)

    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color="grey",
            lineCap="round",
            spaceAfter=5,
            spaceBefore=10,
        )
    )

    total_amount = calculate_ticket_price(order)
    add_to_story(
        story,
        [
            f"Karten regulär: {order.number_regular} à {TICKET_PRICE_REGULAR} €",
            f"Karten ermäßigt: {order.number_discount} à {TICKET_PRICE_DISCOUNT} €",
        ],
    )
    add_space(story)
    add_to_story(story, f"Gesamtsumme: {total_amount} €", STYLE_IMPORTANT)

    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color="grey",
            lineCap="round",
            spaceAfter=5,
            spaceBefore=10,
        )
    )

    add_to_story(
        story,
        "Im ausgewiesenen Betrag ist gemäß § 19 UStG keine Umsatzsteuer enthalten. ",
        STYLE_SMALL,
    )

    add_space(story, height=30)

    story.append(
        Paragraph(
            f"Bitte überweisen Sie den Gesamtbetrag von {total_amount} € innerhalb der nächsten "
            f"{PAYMENT_GRACE_PERIOD_DAYS} Tage auf das folgende Konto. Nur mit der korrekten Eingabe des Verwendungszwecks "
            "ist eine reibungslose Verarbeitung der Zahlung möglich.",
            STYLE_NORMAL,
        )
    )

    add_space(story)

    add_to_story(
        story,
        [
            f"Name: {NAME_ORCHESTRA_FULL}",
            f"IBAN: {IBAN}",
            f"Verwendungszweck: Karten {order.reference_code}",
        ],
    )

    add_space(story)

    add_to_story(
        story,
        [
            "Herzlichen Dank für Ihr Interesse an unserem Konzert.",
            "Wir freuen uns auf Ihren Besuch!",
        ],
    )

    story.append(FrameBreak())

    add_to_story(story, FOOTER_INVOICE, STYLE_SMALL_CENTERED)


def add_to_story(story, lines, style=STYLE_NORMAL):
    if isinstance(lines, str):
        story.append(Paragraph(lines, style))
    else:
        for line in lines:
            story.append(Paragraph(line, style))


def add_space(story, height=12):
    story.append(Spacer(1, height))


def generate_ticket_page(doc, story, order):
    add_to_story(story, "Ihre Tickets", STYLE_HEADING)

    # First print discounted tickets, then regular tickets.
    for i in range(order.number_discount):
        ticket = create_ticket(order, TicketType.DISCOUNT)
        add_to_story(
            story,
            "Die Tickets können entweder ausgedruckt oder digital vorgezeigt werden.",
        )
        add_space(story)
        story.append(TicketFlowable(order, doc.width, ticket))
        story.append(PageBreak())

    for i in range(order.number_regular):
        ticket = create_ticket(order, TicketType.REGULAR)
        add_to_story(
            story,
            "Die Tickets können entweder ausgedruckt oder digital vorgezeigt werden.",
        )
        add_space(story)
        story.append(TicketFlowable(order, doc.width, ticket))
        story.append(PageBreak())
