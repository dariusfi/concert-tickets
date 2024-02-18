from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
import smtplib

import pytz
from ct.constants import EMAIL_PASSWORD, EMAIL_PORT, EMAIL_SERVER, SENDER_EMAIL


def send_email(
    subject: str,
    body: str,
    recipients: list,
    pdf_attachment_content: BytesIO = None,
    attachment_name=None,
    bcc_email: str = None,
):
    if pdf_attachment_content:
        msg = MIMEMultipart()
        msg.attach(MIMEText(body))

        attachment = MIMEApplication(pdf_attachment_content.read(), _subtype="pdf")
        pdf_attachment_content.close()
        attachment.add_header(
            "content-disposition",
            "attachment",
            filename=attachment_name,
        )
        msg.attach(attachment)
    else:
        msg = MIMEText(body)

    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(recipients)

    if bcc_email:
        recipients.append(bcc_email)

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(EMAIL_SERVER, EMAIL_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipients, msg.as_string())


def datetime_as_german_date_str(dt) -> str:
    return dt.astimezone(pytz.timezone("Europe/Berlin")).strftime("%d.%m.%Y")
