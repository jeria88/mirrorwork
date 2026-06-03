import requests
import logging
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

logger = logging.getLogger(__name__)


class BrevoEmailBackend(BaseEmailBackend):
    """Email backend que usa la API REST de Brevo en lugar de SMTP."""

    API_URL = 'https://api.brevo.com/v3/smtp/email'

    def send_messages(self, email_messages):
        api_key = getattr(settings, 'BREVO_API_KEY', '')
        if not api_key:
            logger.error('[Brevo] BREVO_API_KEY no configurada')
            return 0

        sent = 0
        for msg in email_messages:
            try:
                from_email, from_name = self._parse_address(
                    msg.from_email or settings.DEFAULT_FROM_EMAIL
                )
                payload = {
                    'sender': {'name': from_name, 'email': from_email},
                    'to': [{'email': addr} for addr in msg.to],
                    'subject': msg.subject,
                    'textContent': msg.body,
                }
                resp = requests.post(
                    self.API_URL,
                    json=payload,
                    headers={
                        'api-key': api_key,
                        'Content-Type': 'application/json',
                    },
                    timeout=10,
                )
                if resp.status_code in (200, 201):
                    sent += 1
                    logger.info(f'[Brevo] email enviado a {msg.to}')
                else:
                    logger.error(f'[Brevo] error {resp.status_code}: {resp.text}')
                    if not self.fail_silently:
                        raise Exception(f'Brevo API error {resp.status_code}: {resp.text}')
            except Exception as e:
                logger.exception(f'[Brevo] excepción al enviar: {e}')
                if not self.fail_silently:
                    raise
        return sent

    def _parse_address(self, address):
        if '<' in address:
            name, email = address.split('<', 1)
            return email.strip().rstrip('>'), name.strip()
        return address.strip(), 'MirrorWork'
