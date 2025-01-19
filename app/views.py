from django.shortcuts import render
from .models import Probe
import subprocess
import platform
from django.http import JsonResponse
import socket
from datetime import datetime
import paramiko


# Router SSH Details
ROUTER_SSH_DETAILS = {
    "hostname": "23.141.136.2",
    "port": 22,
    "username": "txfiber",
    "password": "southtx956",
}


def main(request):
    probes = Probe.objects.all()
    return render(request, "main.html", {"probes": probes})

def execute_ssh_command(command):
    """
    Execute a command on the router via SSH and return the output.
    """
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=ROUTER_SSH_DETAILS["hostname"],
            port=ROUTER_SSH_DETAILS["port"],
            username=ROUTER_SSH_DETAILS["username"],
            password=ROUTER_SSH_DETAILS["password"],
        )

        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()

        client.close()

        if error:
            raise Exception(error)

        return output.splitlines()

    except Exception as e:
        raise Exception(f"SSH command execution failed: {e}")


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
            # Use traceroute command via SSH
            command = f"traceroute {domain}"
            data = execute_ssh_command(command)
            measurement = "Traceroute from router to resolved IP:"
        elif action == "ping":
            # Use ping command via SSH
            command = (
                f"ping -c 4 {domain}"
                if platform.system() != "Windows"
                else f"ping -n 4 {domain}"
            )
            data = execute_ssh_command(command)
            measurement = "Ping statistics from router:"
        elif action == "dns-lookup":
            # DNS Lookup doesn't need SSH; resolve locally
            data = [f"Resolved {domain} to IP: {ip_address}"]
            measurement = "DNS Lookup Result:"  # No SSH needed
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
