import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def send_email(subject, html_body, recipient_list, text_body=None):
        if not recipient_list:
            return {"success": False, "message": "Recipient email is missing."}

        text_content = text_body or strip_tags(html_body or "")
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            to=recipient_list,
        )
        if html_body:
            email.attach_alternative(html_body, "text/html")

        try:
            result = email.send(fail_silently=False)
            return {
                "success": bool(result),
                "message": "Email sent." if result else "Email not sent.",
            }
        except Exception as exc:
            logger.warning("Email delivery failed: %s", exc)
            return {"success": False, "message": str(exc)}

