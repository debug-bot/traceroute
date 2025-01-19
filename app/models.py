from django.core.exceptions import ValidationError
from django.db import models


# Django model for SSH settings
class SSHSettings(models.Model):
    settings_name = models.CharField(unique=True, max_length=255, help_text="Enter the unique settings name, This will be used to connect to each router/probe", default="default")
    port = models.PositiveIntegerField(default=22)
    username = models.CharField(max_length=255, default="txfiber")
    password = models.CharField(max_length=255, default="southtx956")

    def __str__(self):
        return f"SSH Settings for '{self.settings_name}'"
    
    class Meta:
        verbose_name = "SSH Settings"
        verbose_name_plural = "SSH Settings"

class Router(models.Model):
    TYPE_CHOICES = [
        ("JUNIPER", "Juniper"),
        ("CISCO", "Cisco"),
        ("MIKROTIK", "Mikrotik"),
        ("OTHER", "Other"),
    ]

    VERSION_CHOICES = [
        ("v4", "IPv4"),
        ("v6", "IPv6"),
    ]
    
    ssh_settings = models.ForeignKey(SSHSettings, verbose_name="SSH Settings", on_delete=models.CASCADE)
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        help_text="Select the model of the router, e.g., JUNIPER or Other.",
        verbose_name="Router Model",
    )
    name = models.CharField(
        max_length=100,
        help_text="Enter the unique hostname of the router, e.g., ABC-100.",
        unique=True,
        verbose_name="Router Host Name",
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
        blank=True,
        null=True,
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
        verbose_name = "Router"
        verbose_name_plural = "Routers"
        ordering = ["type", "name"]
        constraints = [
            models.UniqueConstraint(fields=["asn", "ip"], name="unique_asn_ip"),
        ]
