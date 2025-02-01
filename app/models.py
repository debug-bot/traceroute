from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


# Django model for SSH settings
class SSHSettings(models.Model):
    settings_name = models.CharField(unique=True, max_length=255, help_text="Enter the unique settings name, This will be used to connect to each router/probe", default="default")
    port = models.PositiveIntegerField(default=22)
    username = models.CharField(max_length=255, default="txfiber")
    password = models.CharField(max_length=255, default="southtx956")

    def __str__(self):
        return f"SSH Settings: '{self.settings_name}'"
    
    class Meta:
        verbose_name = "SSH Settings"
        verbose_name_plural = "SSH Settings"
        constraints = [
            models.UniqueConstraint(fields=["port","username", "password"], name="unique_settings"),
        ]

class DataCenter(models.Model):
    city = models.CharField(
        max_length=100,
        default="Harlington",
        help_text="Enter the city where the probe is located. Only alphabetic characters are allowed",
        verbose_name="City",
    )
    state = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Enter the state where the probe is located (optional)",
        verbose_name="State",
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Enter the country where the probe is located (optional)",
        verbose_name="Country",
    )
    
    def __str__(self):
        state = ", " + self.state if self.state else ""
        country = ", "+ self.country if self.country else ""
        return self.city + state + country
    def clean(self):
        # Ensure the city contains only alphabetic characters
        if not self.city.replace(" ", "").isalpha():
            raise ValidationError("City name must contain only alphabetic characters")
        
    class Meta:
        verbose_name = "Data Center"
        verbose_name_plural = "Data Centers"
        ordering = ["city"]
        constraints = [
            models.UniqueConstraint(fields=["city", "state"], name="unique_datacenter"),
        ]

class Category(models.Model):
    name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Enter the command category",
        verbose_name="Category Name",
    )
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

class Command(models.Model):
    category = models.ForeignKey(Category, null=True, on_delete=models.CASCADE)
    label = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Enter the command label",
        verbose_name="Label",
    )
    command = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Enter the command",
        verbose_name="Command",
    )
    purpose = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Enter the purpose",
        verbose_name="Purpose",
    )

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
    datacenter = models.ForeignKey(DataCenter, verbose_name="Data Center Location", default=None, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.datacenter}"

    def clean(self):
        """Custom validation logic for advanced constraints."""
        # Ensure the IP matches the selected version
        if self.version == "v4" and ":" in self.ip:
            raise ValidationError("IPv4 address cannot contain colons (:).")
        if self.version == "v6" and "." in self.ip:
            raise ValidationError("IPv6 address cannot contain periods (.).")

    class Meta:
        verbose_name = "Router"
        verbose_name_plural = "Routers"
        ordering = ["type", "name"]
        constraints = [
            models.UniqueConstraint(fields=["asn", "ip"], name="unique_asn_ip"),
        ]


class CommandHistory(models.Model):
    """
    Model to store a history of commands executed by a user.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="command_histories",
        help_text="User who executed the command",
    )
    command = models.TextField(help_text="Command executed by the user")
    timestamp = models.DateTimeField(
        auto_now_add=True, help_text="Timestamp when the command was executed"
    )
    output = models.JSONField(
        blank=True,
        null=True,
        help_text="Output result of the command execution stored as JSON",
    )

    class Meta:
        verbose_name = "Command History"
        verbose_name_plural = "Command Histories"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Command by {self.user.username} on {self.timestamp:%Y-%m-%d %H:%M:%S}"


class PopularCommand(models.Model):
    label = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Enter the command label",
        verbose_name="Label",
    )
    command = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Enter the command",
        verbose_name="Command",
    )
    purpose = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Enter the purpose",
        verbose_name="Purpose",
    )
