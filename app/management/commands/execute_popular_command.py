import sys
from django.core.management.base import BaseCommand
from app.models import Command as CommandModel, PopularCommand


class Command(BaseCommand):
    help = "Execute a command and store it in the PopularCommand model (One-to-One)"

    def add_arguments(self, parser):
        parser.add_argument(
            "command_label", type=str, help="Label of the command to execute"
        )

    def handle(self, *args, **kwargs):
        command_label = (
            kwargs["command_label"].strip().lower()
        )  # Normalize input to lowercase

        # Check if the command exists (case-insensitive)
        try:
            command_obj = CommandModel.objects.get(label__iexact=command_label)
        except CommandModel.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ Command '{command_label}' not found!")
            )
            sys.exit(1)

        # Check if the command is already in PopularCommand
        popular_cmd, created = PopularCommand.objects.update_or_create(
            command=command_obj,
            defaults={"command": command_obj},  # Ensures update works properly
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Command '{command_obj.label}' executed and added to PopularCommand!"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"⚡ Command '{command_obj.label}' was already popular! Timestamp updated."
                )
            )
