import smtplib
import time

SMTP_HOST = "mail.example.com"


def _send(to, subject, body):
    for attempt in range(3):
        try:
            with smtplib.SMTP(SMTP_HOST, timeout=30) as smtp:
                smtp.sendmail("shop@example.com", [to], f"Subject: {subject}\n\n{body}")
            return
        except OSError:
            if attempt == 2:
                raise
            time.sleep(5)


def send_receipt(to, order):
    _send(to, f"Receipt #{order['id']}", f"Total: {order['total']}")


def send_refund_confirmation(to, refund):
    _send(to, "Refund confirmed", f"Refunded: {refund['amount']}")
