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
    summary = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Enter the summary of the category",
        verbose_name="Category Summary",
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Enter the order of the category in accending order",
        verbose_name="Order",
    )
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["order"]
        
    def __str__(self):
        return self.name or "No Category"


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

    def __str__(self):
        return f"{self.label or 'Unnamed Command'} - {self.command or 'No Command'}"


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
    
    STATUS_CHOICES = [ 
        ("online", "Online"),
        ("offline", "Offline"),
        ("warning", "Warning"),
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

    # We store the last 3 pings as "1" for success, "0" for fail. Example: "110", "101", etc.
    last_pings = models.CharField(max_length=3, default="", help_text="Last 3 ping results, '1' for success, '0' for failure.", verbose_name="Last 3 Pings")
    
    # Track how many pings have succeeded vs. total
    total_pings = models.PositiveIntegerField(default=0)
    successful_pings = models.PositiveIntegerField(default=0)
    
    # If the device fails 3 times in a row => offline
    consecutive_failures = models.PositiveIntegerField(default=0, help_text="Number of consecutive failures", verbose_name="Consecutive Failures") 

    # online / warning / offline, based on consecutive failures, 0 => online, 1-2 => warning, >=3 => offline
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="offline", help_text="Current status of the device", verbose_name="Device Status")
        
    last_3_latency = models.JSONField(default=dict, help_text="Last 3 latency values in ms")
    
    # Following 3 fields are in percentage
    cpu_usage = models.FloatField(default=0.0)
    mem_usage = models.FloatField(default=0.0)
    storage_usage = models.FloatField(default=0.0)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def avg_latency(self):
        data = self.last_3_latency or {}
        latencies = data.get("latency", [])
        if len(latencies) == 0:
            return 0.0
        # Compute average
        return round(sum(latencies) / len(latencies), 2)      

    @property
    def uptime_percentage(self):
        """
        Returns how many of the last_pings were '1' (success) as a percentage.
        If last_pings is empty or shorter than 3, we base it on however many pings are stored.
        """
        if not self.last_pings:
            return 0.0
        success_count = self.last_pings.count("1")
        total_count = len(self.last_pings)  # could be 1, 2, or 3
        return (success_count / total_count) * 100.0
    
    def __str__(self):
        return f"{self.name}:{self.ip} - {self.datacenter}"

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

class Configuration(models.Model):
    router = models.ForeignKey(Router, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    version = models.CharField(max_length=200)
    file = models.FileField(upload_to='configuration/')

    def __str__(self):
        return f'{self.router.name} {self.version}'

    class Meta:
        ordering = ['-created_at']


class Latency(models.Model):
    router = models.ForeignKey(Router, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    latency = models.FloatField(help_text="Latency in ms", null=True)

    def __str__(self):
        return f"{self.router.name} - {self.latency} ms at {self.created_at}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Latency'
        verbose_name_plural = 'Latencies'


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
    device = models.ForeignKey(
        Router, 
        on_delete=models.CASCADE,
        null=True,
        default=None,
        related_name="command_history_devices",
        help_text="Device where command was executed",
    )
    command = models.CharField(max_length=500, help_text="Command executed by the user")
    timestamp = models.DateTimeField(
        auto_now_add=True, help_text="Timestamp when the command was executed"
    )
    output = models.TextField(
        default="PING OK",
        help_text="Output result of the command execution",
    )

    class Meta:
        verbose_name = "Command History"
        verbose_name_plural = "Command Histories"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Command by {self.user.username} on {self.timestamp:%Y-%m-%d %H:%M:%S}"


class PopularCommand(models.Model):
    command = models.OneToOneField(
        "Command",
        null=True,
        on_delete=models.CASCADE,
        help_text="Each command can be executed only once in the popular commands list.",
    )
    timestamp = models.DateTimeField(
        auto_now_add=True, help_text="Timestamp when the command was executed"
    )

    def __str__(self):
        return f"Popular Command: {self.command.label if self.command else 'Unknown'} ({self.timestamp.strftime('%Y-%m-%d %H:%M:%S')})"
