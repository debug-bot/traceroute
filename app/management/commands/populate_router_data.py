from django.core.management.base import BaseCommand
from app.models import Router, DataCenter, SSHSettings

DATACENTERS = [
    {"city": "REGION 10	", "state": None, "country": None},
    {"city": "TX FIBER - 305 Datacenter", "state": None, "country": None},
    {"city": "TX FIBER - Edge Routers", "state": None, "country": None},
    {"city": "TXFIBER - H5 Datacenter", "state": None, "country": None},
]

SSH_SETTINGS = [
    {"settings_name": "aochoa", "port": 22, "username": "aochoa", "password": "aochoa84"},
]

ROUTERS = [
    {
        "ssh_settings": SSH_SETTINGS[0]["settings_name"],
        "type": "JUNIPER",
        "name": "TXF.H5.BR1",
        "asn": 400767,
        "ip":"23.141.136.1",
        "version": "v4",
        "datacenter": DATACENTERS[3]["city"]
    },
    {
        "ssh_settings": SSH_SETTINGS[0]["settings_name"],
        "type": "JUNIPER",
        "name": "TXF-HWWS-PE1",
        "asn": 400767,
        "ip":"23.141.136.6",
        "version": "v4",
        "datacenter": DATACENTERS[2]["city"]
    },
    {
        "ssh_settings": SSH_SETTINGS[0]["settings_name"],
        "type": "JUNIPER",
        "name": "TXF-HWWS-PE1",
        "asn": 400767,
        "ip":"23.141.136.2",
        "version": "v4",
        "datacenter": DATACENTERS[1]["city"]
    },
]
    


class Command(BaseCommand):
    help = "Populate the database with routers, data centers, and SSH settings"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting data population..."))

        # Create Data Centers
        data_centers = []
        for datacenter in DATACENTERS:
            try:
                dc = DataCenter.objects.create(**datacenter)
                data_centers.append(dc)
            except:
                pass

        self.stdout.write(
            self.style.SUCCESS(f"✅ Created {len(data_centers)} Data Centers")
        )

        # Create SSH Settings
        ssh_settings_list = []
        for ssh_setting in SSH_SETTINGS:
            try:
                ssh = SSHSettings.objects.create(**ssh_setting)
                ssh_settings_list.append(ssh)
            except:
                pass

        self.stdout.write(
            self.style.SUCCESS(f"✅ Created {len(ssh_settings_list)} SSH Settings")
        )

        # Create Routers
        routers_list = []
        for router in ROUTERS:
            try:
                router["ssh_settings"] = SSHSettings.objects.get(
                    settings_name=router["ssh_settings"]
                )
                router["datacenter"] = DataCenter.objects.get(
                    city=router["datacenter"]
                )
                Router.objects.create(**router)
                routers_list.append(router)
            except:
                pass

        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(routers_list)} Routers"))
