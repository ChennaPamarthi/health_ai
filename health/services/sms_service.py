import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class SMSService:
    def __init__(self):
        self.account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
        self.auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
        self.from_number = getattr(settings, "TWILIO_PHONE_NUMBER", "") or getattr(settings, "TWILIO_FROM_NUMBER", "")

    def _get_client(self):
        if not (self.account_sid and self.auth_token):
            return None

        try:
            from twilio.rest import Client
        except Exception:
            logger.warning("Twilio package is not installed. Run pip install -r requirements.txt.")
            return None

        return Client(self.account_sid, self.auth_token)

    def send_sms(self, to_number, body):
        if not to_number:
            return {"success": False, "message": "Recipient phone number is missing."}

        client = self._get_client()
        if client is None:
            return {"success": False, "message": "Twilio client is not configured or the twilio package is not installed."}

        try:
            message = client.messages.create(
                body=body,
                from_=self.from_number,
                to=to_number,
            )
            return {
                "success": True,
                "message": "SMS sent.",
                "sid": getattr(message, "sid", ""),
            }
        except Exception as exc:
            logger.warning("SMS delivery failed: %s", exc)
            return {"success": False, "message": str(exc)}
