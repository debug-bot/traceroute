from django.shortcuts import render
from .models import Category, DataCenter, Router, SSHSettings
import platform
from django.http import JsonResponse
import socket
from datetime import datetime
from .utils import execute_ssh_command, install_package_if_missing, ROUTER_SSH_DETAILS
import time
import paramiko


def main(request):
    routers = Router.objects.all()
    return render(request, "main.html", {"routers": routers})


def test_ssh_connection(request):
    """
    Test if the SSH connection to the router is working.
    """
    try:
        # Test command (e.g., check hostname or uptime)
        test_command = "ping 8.8.8.8"
        output = execute_ssh_command(test_command)
        return JsonResponse(
            {
                "status": "success",
                "message": "SSH connection successful.",
                "data": output,
            }
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def network_tools_api(request):
    # Get the 'action' and 'domain' from query parameters
    router_id = request.GET.get("router_id", "")
    command = request.GET.get("command", "")
    custom = request.GET.get("custom", False)

    # from the router_id, get the router object
    router = Router.objects.filter(id=router_id).first()

    # get the router's ip address and add to the ROUTER_SSH_DETAILS
    if router:
        ROUTER_SSH_DETAILS["hostname"] = router.ip
        ROUTER_SSH_DETAILS["password"] = router.ssh_settings.password
        ROUTER_SSH_DETAILS["username"] = router.ssh_settings.username
        ROUTER_SSH_DETAILS["port"] = router.ssh_settings.port

    if not command:
        return JsonResponse(
            {
                "status": "error",
                "message": "The 'command' query parameter is required.",
            },
            status=400,
        )

    if custom:
        print("Custom Command")

    try:
        # Resolve the domain to IP address if action is not custom

        timestamp = (
            f"STARTED QUERY AT {datetime.utcnow().strftime('%Y/%m/%d %H:%M:%S')} UTC"
        )

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=ROUTER_SSH_DETAILS["hostname"],
                port=ROUTER_SSH_DETAILS["port"],
                username=ROUTER_SSH_DETAILS["username"],
                password=ROUTER_SSH_DETAILS["password"],
            )

            # Execute the traceroute command
            channel = client.get_transport().open_session()
            channel.exec_command(command)

            # Wait for 20 seconds
            time.sleep(20)

            # Send CTRL+C to stop the traceroute
            # channel.send("\x03")  # CTRL+C
            output = channel.recv(65535).decode()  # Get remaining output

            data = output.splitlines()
            measurement = "Statistics from router:"
            channel.close()
            client.close()
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Command failed: {e}"}, status=400
            )

        # Format the output
        response = {
            "status": "success",
            "timestamp": timestamp,
            "measurement": measurement,
            "data": data,
        }
        return JsonResponse(response)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def dashboard(request):
    unique_cities =  [
                    f"{city}, {state}" if state else f"{city}"
                    for city, state in DataCenter.objects.values_list("city", "state").distinct().order_by("city")
                ]
    categories = (
        Category.objects.prefetch_related("command_set")
        .filter(command__isnull=False)
        .distinct()
    )
    return render(
        request,
        "dashboard.html",
        {"unique_cities": unique_cities, "categories": categories},
    )


def get_devices_by_cities(request):
    if request.method == "GET":
        cities = request.GET.getlist("cities[]")  # Get the selected cities as a list
        city_names = [entry.split(",")[0] for entry in cities]  # Extract only city names

        devices = Router.objects.filter(datacenter__city__in=city_names).values("id", "name", "ip")
        return JsonResponse({"devices": list(devices)})
    return JsonResponse({"error": "Invalid request method"}, status=400)
