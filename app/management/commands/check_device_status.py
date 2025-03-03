# yourapp/management/commands/check_device_status.py

import subprocess
from django.core.management.base import BaseCommand
from app.models import Router
from app.utils import get_cpu_and_mem, get_storage  # or wherever your SSH funcs are


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

def update_last_pings(router, success):
    old_pings = router.last_pings or ""
    # keep only the last 2 results, then append the new one
    old_pings = old_pings[-2:]
    new_ping = "1" if success else "0"
    router.last_pings = old_pings + new_ping

def derive_status_from_pings(last_pings):
    # If we have fewer than 3 pings so far, treat as 'offline' 
    if len(last_pings) < 3:
        status = "0"  # default to offline if no pings yet
        if len(last_pings) > 0:
            status = last_pings[-1]
        return "offline" if status == "0" else "online"
    fails = last_pings.count("0")
    if fails == 3:
        return "offline"
    elif fails == 0:
        return "online"
    else:
        return "warning"

class Command(BaseCommand):
    help = "Ping each device, update status based on last 3 pings, also fetch CPU/mem/storage"

    def handle(self, *args, **options):
        routers = Router.objects.all()
        for router in routers:
            success = ping_device_once(router.ip)
            
            # 1) Shift last_pings and add new result
            update_last_pings(router, success)

            # 2) Derive new status
            router.status = derive_status_from_pings(router.last_pings)
            
            # 3) Update total pings
            router.total_pings += 1
            if success:
                router.successful_pings += 1
                # Reset consecutive failures
                router.consecutive_failures = 0

            else:
                router.consecutive_failures += 1
            
            # 4) Update CPU, memory, storage usage
            try:
                # 1) Get CPU + memory usage
                cpu_usage, mem_usage = get_cpu_and_mem(router.ip)
                self.stdout.write(self.style.SUCCESS(
                    f"[{router.name}:{router.ip}] CPU={cpu_usage}%, MEM={mem_usage}%"
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"[{router.name}:{router.ip}] Error getting CPU/MEM usage: {e}"
                ))
                cpu_usage, mem_usage = 0, 0
            
            try:
                # 2) Get storage usage
                _, overall_storage_pct = get_storage(router.ip)
                self.stdout.write(self.style.SUCCESS(
                    f"[{router.name}:{router.ip}] Storage={overall_storage_pct}%"
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"[{router.name}:{router.ip}] Error getting storage usage: {e}"
                ))
                overall_storage_pct = 0

            # 5) Update router fields
            router.cpu_usage = cpu_usage or 0.0
            router.mem_usage = mem_usage or 0.0
            router.storage_usage = overall_storage_pct or 0.0
            
            router.save()

            # 6) Optional: If router goes offline, send an alert
            if router.status == 'offline':
                self.stdout.write(self.style.WARNING(
                    f"[ALERT] {router.name}:{router.ip} is offline!"
                ))

        self.stdout.write(self.style.SUCCESS("Device status check complete."))
