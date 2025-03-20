import time
import paramiko
import os
import hashlib
import datetime
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from app.models import TYPE_CHOICES, ConfigurationBackupHistory, Router, Configuration
from app.utils import compare_and_return_changes_text, send_alert_email


class Command(BaseCommand):
    help = "Fetch 'show configuration | display set' from each router. If changed, store a new version."

    def handle(self, *args, **options):
        command = "show configuration | display set"
        routers = Router.objects.filter(only_monitor=False).all()
        for router in routers:
            self.stdout.write(
                self.style.NOTICE(
                    f"Checking configuration for {router.name} ({router.ip})..."
                )
            )

            # 1) Fetch the config via SSH
            try:
                # Set up the SSH client and connect using the router's details
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=router.ip,
                    port=router.ssh_settings.port,
                    username=router.ssh_settings.username,
                    password=router.ssh_settings.password,
                )
                channel = client.get_transport().open_session()
                channel.exec_command(command)
                collected_output = ""
                start_time = time.time()
                try:
                    # Loop until the command finishes or a 20-second timeout is reached.
                    while True:
                        if channel.recv_ready():
                            chunk = channel.recv(1024).decode()
                            collected_output += chunk
                        if channel.exit_status_ready():
                            break
                        if time.time() - start_time >= 20:
                            collected_output += "\nTimeout reached (20 seconds). Closing connection...\n"
                            break
                        time.sleep(1)
                    # Flush any remaining output.
                    while channel.recv_ready():
                        chunk = channel.recv(1024).decode()
                        collected_output += chunk
                except Exception as e:
                    collected_output += (
                        f"\nConnection aborted: {e}. Terminating SSH session.\n"
                    )
                finally:
                    channel.close()
                    client.close()
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to get config for {router.name}: {e}")
                )
                continue

            # Convert config_text to a standard string or list of lines as needed
            if not collected_output:
                self.stdout.write(
                    self.style.WARNING(f"No output for {router.name}. Skipping.")
                )
                continue

            config_text = collected_output

            # 2) Compare with the latest stored config
            last_config = (
                Configuration.objects.filter(router=router)
                .order_by("-created_at")
                .first()
            )
            if last_config:
                # Read the file from FileField and compare
                with last_config.file.open("r") as f:
                    old_config_text = f.read()

                # If they match exactly, skip
                if old_config_text.strip() == config_text.strip():
                    self.stdout.write(
                        self.style.SUCCESS(f"No change for {router.name}.")
                    )
                    # Update only created_at field
                    last_config.created_at = timezone.now()
                    last_config.save()
                    
                    # Update Configuration History Model
                    ConfigurationBackupHistory.objects.create(
                        configuration=last_config,
                        success=True,
                        created_at=last_config.created_at
                    )
                    # Skip to the next router
                    continue

                else:
                    # Compare the old and new configuration texts.
                    changes_old, changes_new = compare_and_return_changes_text(
                        old_config_text, config_text
                    )

                    # Build an email message with the changes.
                    email_body = (
                        f"Configuration changes detected for {router.name}:\n\n"
                    )
                    email_body += "Changed lines in the OLD configuration:\n"
                    email_body += (
                        "\n".join([repr(line) for line in changes_old]) + "\n\n"
                    )
                    email_body += "Changed lines in the NEW configuration:\n"
                    email_body += "\n".join([repr(line) for line in changes_new])

                    # Send the email (customize sender, recipients, etc. as needed).
                    send_alert_email(
                        alert_type="CONFIGURATION",
                        subject=f"Configuration Update for {router.name} ({router.ip})",
                        message=email_body,
                    )

            # 3) If different (or no previous config), store a new version
            #    We'll make a simple version scheme like "vYYYYMMDD-HHMMSS"
            new_version = timezone.now().strftime("v%Y%m%d-%H%M%S")
            now = timezone.now()

            config_obj = Configuration(router=router, version=new_version, created_at=now)

            # 4) Save the config text to the FileField
            #    We'll name it something like "routerID_version.txt"
            filename = f"{router.name}_{router.ip}_{new_version}.txt"
            config_obj.file.save(
                filename, ContentFile(config_text)  # Wrap the string in a ContentFile
            )
            

            config_obj.save()
            
            # Update Configuration History Model
            ConfigurationBackupHistory.objects.create(
                configuration=config_obj,
                success=True,
                created_at=now
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Stored new config for {router.name} as version {new_version}."
                )
            )

        self.stdout.write(self.style.SUCCESS("Done updating device configs."))
