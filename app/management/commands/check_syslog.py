import os
import re
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail

from app.models import TYPE_CHOICES, Alert
from app.utils import send_alert_email


class Command(BaseCommand):
    help = "Checks a syslog file for specific keywords (e.g., BGP, OSPF) and sends an email alert if found."

    def add_arguments(self, parser):
        parser.add_argument(
            "log_file", type=str, help="Path to the syslog file to be scanned."
        )

    def handle(self, *args, **options):
        log_file = options["log_file"]
        Alert.objects.create(type="SYSLOG",subject=log_file,message='Test')
        self.stdout.write(f"Started check_syslog, {log_file}")

        if not os.path.exists(log_file):
            raise CommandError(f"Log file {log_file} does not exist.")

        keywords_str = "BGP, OSPF"  # Keywords as a comma-separated string
        keywords = [kw.strip() for kw in keywords_str.split(",")]
        pattern = re.compile("|".join(keywords), re.IGNORECASE)

        matching_lines = []

        # Read the log file and search for keywords.
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                # if pattern.search(line):
                matching_lines.append(line.strip())

        if matching_lines:
            email_subject = (
                f"Alert: Syslog contains keywords for {os.path.basename(log_file)}"
            )
            email_body = (
                f"The following log lines in {log_file} match the keywords ({', '.join(keywords)}):\n\n"
                + "\n".join(matching_lines)
            )

            # Send the email (customize from_email and recipient_list as needed).
            send_alert_email(
                alert_type="SYSLOG",
                subject=email_subject,
                message=email_body,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Email sent with {len(matching_lines)} matching log lines."
                )
            )
        else:
            self.stdout.write("No matching log lines found.")
