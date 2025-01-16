"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

application = get_wsgi_application()


# from app.models import Probe
# import random


# # Generate dummy data for probes
# def create_dummy_probes():
#     # Types of probes
#     types = ["RIPE", "OTHER"]

#     # Cities, states, and countries
#     locations = [
#         ("Lexington", "Massachusetts", "US"),
#         ("Seven Corners", "Virginia", "US"),
#         ("Fairfax Station", "Virginia", "US"),
#         ("Toronto", "Ontario", "CA"),
#         ("London", "England", "UK"),
#     ]

#     # Create 10 IPv4 probes
#     for i in range(10):
#         city, state, country = random.choice(locations)
#         Probe.objects.create(
#             type=random.choice(types),
#             name=f"Probe_v4_{i+1}",
#             asn=random.randint(100, 999),
#             ip=f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}",
#             version="v4",
#             city=city,
#             state=state,
#             country=country,
#         )

#     # Create 10 IPv6 probes
#     for i in range(10):
#         city, state, country = random.choice(locations)
#         Probe.objects.create(
#             type=random.choice(types),
#             name=f"Probe_v6_{i+1}",
#             asn=random.randint(100, 999),
#             ip=f"{random.randint(1, 65535):x}:{random.randint(1, 65535):x}:{random.randint(1, 65535):x}:{random.randint(1, 65535):x}:{random.randint(1, 65535):x}:{random.randint(1, 65535):x}:{random.randint(1, 65535):x}:{random.randint(1, 65535):x}",
#             version="v6",
#             city=city,
#             state=state,
#             country=country,
#         )

#     print("Dummy data for v4 and v6 probes created successfully!")


# # Run the function
# create_dummy_probes()
