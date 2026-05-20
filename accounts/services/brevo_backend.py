import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import sanitize_address

class BrevoApiEmailBackend(BaseEmailBackend):
    """
    A Django Email Backend that sends emails via Brevo's HTTP API.
    Used to bypass SMTP port blocking on environments like Render.
    """
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_url = "https://api.brevo.com/v3/smtp/email"
        # In this backend, EMAIL_HOST_PASSWORD should be your Brevo API Key
        self.api_key = getattr(settings, 'EMAIL_HOST_PASSWORD', None)

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        
        count = 0
        for message in email_messages:
            if self._send(message):
                count += 1
        return count

    def _send(self, email_message):
        """A helper method that does the actual sending."""
        if not email_message.recipients():
            return False
        
        from_email = sanitize_address(email_message.from_email, email_message.encoding)
        recipients = [sanitize_address(addr, email_message.encoding) for addr in email_message.to]
        
        payload = {
            "sender": {"email": from_email},
            "to": [{"email": addr} for addr in recipients],
            "subject": email_message.subject,
            "textContent": email_message.body,
        }

        # Handle HTML content if present
        if hasattr(email_message, 'alternatives') and email_message.alternatives:
            for content, mimetype in email_message.alternatives:
                if mimetype == 'text/html':
                    payload["htmlContent"] = content
                    break

        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            if response.status_code in [201, 202]:
                return True
            
            if not self.fail_silently:
                response.raise_for_status()
        except Exception:
            if not self.fail_silently:
                raise
            return False
        
        return False
