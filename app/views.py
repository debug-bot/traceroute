from django.shortcuts import render
from .models import Probe
import subprocess
import platform
from django.http import JsonResponse
import socket
from datetime import datetime


def main(request):
    probes = Probe.objects.all()
    return render(request, "main.html", {"probes": probes})


def network_tools_api(request):
    # Get the 'action' and 'domain' from query parameters
    action = request.GET.get("action", "").lower()
    domain = request.GET.get("domain", "")

    if not action or not domain:
        return JsonResponse(
            {
                "status": "error",
                "message": "Both 'action' and 'domain' query parameters are required.",
            }
        )

    try:
        # Resolve the domain to IP address
        try:
            ip_address = socket.gethostbyname(domain)
        except socket.gaierror:
            return JsonResponse(
                {"status": "error", "message": f"Cannot resolve {domain}."}, status=400
            )

        # Add resolved IP and timestamp
        resolved_info = f"RESOLVED {domain} TO {ip_address}"
        timestamp = (
            f"STARTED QUERY AT {datetime.utcnow().strftime('%Y/%m/%d %H:%M:%S')} UTC"
        )

        if action == "traceroute":
            # Use tracert for Windows and traceroute for Linux/Unix
            command = (
                ["tracert", domain]
                if platform.system() == "Windows"
                else ["traceroute", domain]
            )
            result = subprocess.run(command, capture_output=True, text=True)
            data = result.stdout.splitlines()
            measurement = "Traceroute from local host to resolved IP:"
        elif action == "ping":
            # Use appropriate ping options for Windows and Linux
            if platform.system() == "Windows":
                command = ["ping", "-n", "4", domain]
            else:
                command = ["ping", "-c", "4", domain]
            result = subprocess.run(command, capture_output=True, text=True)
            data = result.stdout.splitlines()
            measurement = "Ping statistics:"
        elif action == "dns-lookup":
            # Return resolved IP address in a similar format
            data = [f"Resolved {domain} to IP: {ip_address}"]
            measurement = "DNS Lookup Result:"
        else:
            return JsonResponse(
                {"status": "error", "message": f"Unknown action '{action}'."},
                status=400,
            )

        # Format the output
        response = {
            "status": "success",
            "resolved": resolved_info,
            "timestamp": timestamp,
            "measurement": measurement,
            "data": data,
        }
        return JsonResponse(response)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
