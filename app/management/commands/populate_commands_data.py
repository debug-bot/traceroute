import random
from django.core.management.base import BaseCommand
from app.models import Category, Command


class Command(BaseCommand):
    help = "Populate the database with categories and commands"

    def handle(self, *args, **kwargs):
        self.stdout.write(
            self.style.SUCCESS("🚀 Populating categories and commands...")
        )

        # Define categories and their respective commands
        all_commands = [
            # Routing & Protocols
            (
                "Routing & Protocols",
                [
                    (
                        "Check Routing Table",
                        "show route",
                        "Displays the current routing table.",
                    ),
                    ("Check BGP Neighbors", "show bgp summary", "Shows status of BGP peers."),
                    (
                        "Check BGP Routes for Prefix",
                        "show route protocol bgp",
                        "Lists routes learned via BGP.",
                    ),
                    (
                        "Check OSPF Neighbors",
                        "show ospf neighbor",
                        "Displays OSPF adjacency information.",
                    ),
                    (
                        "Check ISIS Neighbors",
                        "show isis adjacency",
                        "Displays ISIS neighbor relationships.",
                    ),
                    (
                        "Check Static Routes",
                        "show route protocol static",
                        "Lists manually configured static routes.",
                    ),
                ],
            ),
            # Troubleshooting
            (
                "Troubleshooting",
                [
                    (
                        "Run Ping",
                        "ping <destination>",
                        "Sends ICMP packets to check connectivity.",
                    ),
                    (
                        "Run Traceroute",
                        "traceroute <destination>",
                        "Displays the path packets take to a host.",
                    ),
                    (
                        "Check Interface Traffic Stats",
                        "show interfaces extensive",
                        "Displays detailed interface statistics.",
                    ),
                    (
                        "Check Dropped Packets",
                        "show firewall filter <filter-name>",
                        "Lists packets dropped by firewall rules.",
                    ),
                    (
                        "Check High CPU Processes",
                        "show system processes extensive",
                        "Matches CPU processes.",
                    ),
                    (
                        "Monitor Real-Time Traffic",
                        "monitor traffic interface <interface>",
                        "Live packet capture on an interface.",
                    ),
                    (
                        "Check Packet Flow",
                        "show security flow session",
                        "Displays active flow sessions in the firewall.",
                    ),
                ],
            ),
            # Interfaces & Connectivity
            (
                "Interfaces & Connectivity",
                [
                    (
                        "Check Interface Status",
                        "show interfaces terse",
                        "Summarized view of interface states.",
                    ),
                    (
                        "Check Interface Descriptions",
                        "show interfaces descriptions",
                        "Lists interface descriptions.",
                    ),
                    ("Check Interface Errors", "show interfaces extensive", "Match errors."),
                    (
                        "Check Interfaces with High Drops",
                        "show interfaces extensive",
                        "Match 'input error'.",
                    ),
                    (
                        "Check MAC Address Table",
                        "show ethernet-switching table",
                        "Displays learned MAC addresses.",
                    ),
                    (
                        "Check LLDP Neighbors",
                        "show lldp neighbors",
                        "Displays LLDP-discovered neighbors.",
                    ),
                    ("Check ARP Table", "show arp", "Lists ARP cache entries."),
                ],
            ),
            # System Health
            (
                "System Health",
                [
                    ("Check System Uptime", "show system uptime", "Displays router uptime."),
                    (
                        "Check CPU & Memory Usage",
                        "show system processes extensive",
                        "Shows CPU/memory utilization.",
                    ),
                    ("Check Active Alarms", "show system alarms", "Lists any system alerts."),
                    (
                        "Check Environmental Sensors",
                        "show chassis environment",
                        "Displays temperature, fans, and sensors.",
                    ),
                    (
                        "Check Power Supply Status",
                        "show chassis power",
                        "Checks power supply health.",
                    ),
                    (
                        "Check Chassis Hardware",
                        "show chassis hardware",
                        "Lists router hardware components.",
                    ),
                    (
                        "Check Current Logged-in Users",
                        "show system users",
                        "Displays active SSH/Telnet sessions.",
                    ),
                    (
                        "Check NTP Sync Status",
                        "show ntp status",
                        "Checks if NTP time synchronization is working.",
                    ),
                    (
                        "Check Logs (Last 50 Lines)",
                        "show log messages last 50",
                        "Displays the last 50 log messages.",
                    ),
                ],
            ),
            # Configuration
            (
                "Configuration",
                [
                    (
                        "Check Interface Configuration",
                        "show configuration interfaces",
                        "Displays interface configuration.",
                    ),
                    (
                        "Check BGP Configuration",
                        "show configuration protocols bgp",
                        "Displays BGP configuration.",
                    ),
                    (
                        "Check OSPF Configuration",
                        "show configuration protocols ospf",
                        "Displays OSPF configuration.",
                    ),
                    (
                        "Check ISIS Configuration",
                        "show configuration protocols isis",
                        "Displays ISIS configuration.",
                    ),
                    (
                        "Check VLAN Configuration",
                        "show configuration vlans",
                        "Displays VLAN settings.",
                    ),
                    (
                        "Check Firewall Configuration",
                        "show configuration firewall",
                        "Displays firewall rule settings.",
                    ),
                    (
                        "Check SNMP Configuration",
                        "show configuration snmp",
                        "Displays SNMP monitoring settings.",
                    ),
                    (
                        "Check NTP Configuration",
                        "show configuration system ntp",
                        "Displays NTP settings.",
                    ),
                    (
                        "Check Logging Configuration",
                        "show configuration system syslog",
                        "Displays syslog logging settings.",
                    ),
                ],
            ),
            # FastCLI Predefined Commands
            (
                "FastCLI Predefined",
                [
                    ("Check System Uptime", "show system uptime", "Displays router uptime."),
                    (
                        "Check Interface Descriptions",
                        "show interfaces descriptions",
                        "Shows interface descriptions.",
                    ),
                    ("Check Interface Errors", "show interfaces extensive", "Match errors."),
                    (
                        "Check Interface Status",
                        "show interfaces terse",
                        "Summarized view of interface states.",
                    ),
                    ("Check Routing Table", "show route", "Displays routing table."),
                    (
                        "Check BGP Neighbors",
                        "show bgp summary",
                        "Summarized view of BGP sessions.",
                    ),
                    (
                        "Check BGP Routes for Prefix",
                        "show route protocol bgp",
                        "Lists BGP-learned routes.",
                    ),
                    (
                        "Check OSPF Neighbors",
                        "show ospf neighbor",
                        "Displays OSPF adjacency info.",
                    ),
                    (
                        "Check ISIS Neighbors",
                        "show isis adjacency",
                        "Displays ISIS neighbor relationships.",
                    ),
                    ("Check ARP Table", "show arp", "Displays ARP entries."),
                    (
                        "Check MAC Address Table",
                        "show ethernet-switching table",
                        "Displays MAC learning table.",
                    ),
                    (
                        "Check LLDP Neighbors",
                        "show lldp neighbors",
                        "Displays LLDP-discovered neighbors.",
                    ),
                    (
                        "Check CPU & Memory Usage",
                        "show system processes extensive",
                        "Shows CPU/memory usage details.",
                    ),
                    (
                        "Check Current Users Logged In",
                        "show system users",
                        "Lists logged-in users.",
                    ),
                    (
                        "Check NTP Sync Status",
                        "show ntp status",
                        "Displays NTP synchronization details.",
                    ),
                    (
                        "Check Logs (Last 50 Lines)",
                        "show log messages last 50",
                        "Displays the last 50 log messages.",
                    ),
                    (
                        "Check Active Alarms",
                        "show system alarms",
                        "Displays active system alarms.",
                    ),
                    (
                        "Check Chassis Hardware",
                        "show chassis hardware",
                        "Lists hardware components.",
                    ),
                    (
                        "Check Environmental Sensors",
                        "show chassis environment",
                        "Displays fan, PSU, and temperature status.",
                    ),
                    (
                        "Check Power Supply Status",
                        "show chassis power",
                        "Shows power supply status.",
                    ),
                    (
                        "Check Interfaces with High Drops",
                        "show interfaces extensive",
                        "Match 'input error'.",
                    ),
                ],
            ),
        ]

        # Insert all commands into the database
        for category_name, command_list in all_commands:
            category, created = Category.objects.get_or_create(name=category_name)

            for label, command, purpose in command_list:
                Command.objects.get_or_create(
                    category=category,
                    label=label,
                    command=command,
                    purpose=purpose,
                )

        self.stdout.write(
            self.style.SUCCESS("✅ All categories and commands successfully populated!")
        )
