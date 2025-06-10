import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from .celery_app import celery_app
from app.core.config import settings
from loguru import logger
import os
from email import encoders



def send_email(email_to: str, subject: str, body: str, attachment_path: str = None):
    msg = MIMEMultipart()
    msg["From"] = settings.MAIL_USERNAME
    msg["To"] = email_to
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "html", "utf-8"))

    if attachment_path:
        with open(attachment_path, "rb") as attachment:
            file_name = os.path.basename(attachment_path)
            if file_name.endswith(".xlsx"):
                part = MIMEBase('application', "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{file_name}"')
                msg.attach(part)

            elif file_name.endswith(".pdf"):
                part = MIMEApplication(attachment.read(), Name=file_name)
                part['Content-Disposition'] = f'attachment; filename="{file_name}"'
                msg.attach(part)

    logger.info(f"Sending email to {email_to}")
    logger.info(f"Message: {msg.as_string().encode('utf-8', 'replace').decode('utf-8')}")


    try:
        with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            server.starttls()
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.sendmail(settings.MAIL_USERNAME, email_to, msg.as_string())
    except Exception as e:
        print(f"Failed to send email: {e}")


@celery_app.task(name="send_email_task")
def send_email_task(email_to: str, subject: str, body: str, attachment_path: str = None):
    send_email(email_to, subject, body, attachment_path)
