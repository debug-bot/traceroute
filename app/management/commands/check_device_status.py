# yourapp/management/commands/check_device_status.py

import subprocess
from django.core.management.base import BaseCommand
from app.models import Router
from app.utils import get_device_stats


def ping_device_once(ip_address):
    """
    Returns True if single ping is successful, False otherwise.
    Adjust the command for Windows (-n 1) or Linux/Mac (-c 1).
    """
    try:
        subprocess.check_output(
            ["ping", "-c", "1", "-W", "1", ip_address],
            stderr=subprocess.STDOUT
        )
        return True
    except subprocess.CalledProcessError:
        return False

class Command(BaseCommand):
    help = "Ping each device, update uptime and status"

    def handle(self, *args, **options):
        routers = Router.objects.all()
        for router in routers:
            success = ping_device_once(router.ip)
            
            # Update total pings
            router.total_pings += 1
            if success:
                router.successful_pings += 1
                # Reset consecutive failures
                router.consecutive_failures = 0

                # If we had failures but now success => warning or online
                if router.status == 'offline' or router.status == 'warning':
                    # You could decide to put it in 'warning' if you want a "recovering" state
                    # or directly to 'online'
                    router.status = 'warning' if router.consecutive_failures > 0 else 'online'
                else:
                    router.status = 'online'
            else:
                router.consecutive_failures += 1
                if router.consecutive_failures >= 3:
                    router.status = 'offline'
                else:
                    # Some partial failures => warning
                    router.status = 'warning'
            
            # Update CPU, memory, storage usage
            try:
                cpu_usage, mem_usage, storage_usage = get_device_stats(router.ip)
                self.stdout.write(self.style.SUCCESS(
                    f"[{router.name}:{router.ip}] CPU={cpu_usage}%, MEM={mem_usage}%, Storage={storage_usage}%"
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"[{router.name}:{router.ip}] Error getting CPU/MEM and Storage usage: {e}"
                ))
                cpu_usage, mem_usage, storage_usage = 0, 0, 0
            
            # Update router fields
            router.cpu_usage = cpu_usage or 0.0
            router.mem_usage = mem_usage or 0.0
            router.storage_usage = storage_usage or 0.0
            
            router.save()

            # Optional: If router goes offline, send an alert
            if router.status == 'offline':
                self.stdout.write(self.style.WARNING(
                    f"[ALERT] {router.name}:{router.ip} is offline!"
                ))

        self.stdout.write(self.style.SUCCESS("Device status check complete."))
