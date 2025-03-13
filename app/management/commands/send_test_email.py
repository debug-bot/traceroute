from django.core.management.base import BaseCommand
from django.core.mail import send_mail

class Command(BaseCommand):
    help = "Send a test email using the SMTP relay configuration"

    def handle(self, *args, **kwargs):
        try:
            send_mail(
                'Test Email Subject',
                'This is a test email message.',
                'alerts@fastcli.com',
                ['adnanashraf4423@gmail.com'],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS("Test email sent successfully."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send test email: {e}"))
