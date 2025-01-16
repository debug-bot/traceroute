from django.core.exceptions import ValidationError
from django.db import models


class Probe(models.Model):
    TYPE_CHOICES = [
        ("RIPE", "RIPE"),
        ("OTHER", "Other"),
    ]

    VERSION_CHOICES = [
        ("v4", "IPv4"),
        ("v6", "IPv6"),
    ]

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        help_text="Select the type of the probe, e.g., RIPE or Other.",
        verbose_name="Probe Type",
    )
    name = models.CharField(
        max_length=100,
        help_text="Enter the unique name of the probe, e.g., Probe #100.",
        unique=True,
        verbose_name="Probe Name",
    )
    asn = models.PositiveIntegerField(
        help_text="Enter the Autonomous System Number (ASN) of the probe. Must be a valid ASN.",
        verbose_name="Autonomous System Number",
    )
    ip = models.GenericIPAddressField(
        help_text="Enter a valid IP address of the probe (IPv4 or IPv6).",
        verbose_name="IP Address",
        protocol="both",  # Allows both IPv4 and IPv6
    )
    version = models.CharField(
        max_length=2,
        choices=VERSION_CHOICES,
        help_text="Specify whether the IP version is IPv4 or IPv6. Ensure it matches the IP format.",
        verbose_name="IP Version",
    )
    city = models.CharField(
        max_length=100,
        help_text="Enter the city where the probe is located. Only alphabetic characters are allowed.",
        verbose_name="City",
    )
    state = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Enter the state where the probe is located (optional).",
        verbose_name="State",
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Enter the country where the probe is located (optional).",
        verbose_name="Country",
    )

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state or ''}, {self.country or ''}"

    def clean(self):
        """Custom validation logic for advanced constraints."""
        # Ensure the IP matches the selected version
        if self.version == "v4" and ":" in self.ip:
            raise ValidationError("IPv4 address cannot contain colons (:).")
        if self.version == "v6" and "." in self.ip:
            raise ValidationError("IPv6 address cannot contain periods (.).")

        # Ensure the city contains only alphabetic characters
        if not self.city.replace(" ", "").isalpha():
            raise ValidationError("City name must contain only alphabetic characters.")

    class Meta:
        verbose_name = "Probe"
        verbose_name_plural = "Probes"
        ordering = ["type", "name"]
        constraints = [
            models.UniqueConstraint(fields=["asn", "ip"], name="unique_asn_ip"),
        ]
