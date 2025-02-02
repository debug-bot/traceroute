import random
from django.core.management.base import BaseCommand
from faker import Faker
from app.models import Router, DataCenter, SSHSettings

fake = Faker()


class Command(BaseCommand):
    help = "Populate the database with random routers, data centers, and SSH settings"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting data population..."))

        # Create Data Centers
        data_centers = []
        for _ in range(5):  # Creating 5 data centers
            dc = DataCenter.objects.create(
                city=fake.city(),
                state=fake.state(),
                country=fake.country(),
            )
            data_centers.append(dc)

        self.stdout.write(
            self.style.SUCCESS(f"✅ Created {len(data_centers)} Data Centers")
        )

        # Create SSH Settings
        ssh_settings_list = []
        for _ in range(5):  # Creating 5 SSH settings
            ssh = SSHSettings.objects.create(
                settings_name=fake.unique.word(),
                port=random.choice([22, 2222, 8022]),
                username=fake.user_name(),
                password=fake.password(),
            )
            ssh_settings_list.append(ssh)

        self.stdout.write(
            self.style.SUCCESS(f"✅ Created {len(ssh_settings_list)} SSH Settings")
        )

        # Create Routers
        router_types = ["JUNIPER", "CISCO", "MIKROTIK", "OTHER"]
        ip_versions = ["v4", "v6"]

        for _ in range(10):  # Creating 10 routers
            ip_version = random.choice(ip_versions)
            ip_address = fake.ipv4() if ip_version == "v4" else fake.ipv6()

            Router.objects.create(
                ssh_settings=random.choice(ssh_settings_list),
                type=random.choice(router_types),
                name=fake.unique.word().upper(),
                asn=random.randint(1000, 99999),
                ip=ip_address,
                version=ip_version,
                datacenter=random.choice(data_centers),
            )

        self.stdout.write(self.style.SUCCESS("✅ Successfully populated routers!"))
