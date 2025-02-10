from django.shortcuts import render, redirect
from .models import (
    Category,
    CommandHistory,
    DataCenter,
    PopularCommand,
    Router,
    SSHSettings,
)
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from datetime import datetime
from .utils import execute_ssh_command, ROUTER_SSH_DETAILS
import time
import paramiko
from django.contrib.auth.decorators import login_required
from django.utils.html import format_html
import json


def main(request):
    return redirect("login")


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


@login_required(login_url="/login")
def network_tools_api(request):
    # Get query parameters
    router_id = request.GET.get("router_id", "")
    command = request.GET.get("command", "")
    # Convert custom parameter to boolean.
    # (Assumes custom is passed as "true" or "false".)
    custom_param = request.GET.get("custom", "false").lower() == "true"

    # Retrieve the router object based on router_id
    router = Router.objects.filter(id=router_id).first()
    if router:
        ROUTER_SSH_DETAILS["hostname"] = router.ip
        ROUTER_SSH_DETAILS["password"] = router.ssh_settings.password
        ROUTER_SSH_DETAILS["username"] = router.ssh_settings.username
        ROUTER_SSH_DETAILS["port"] = router.ssh_settings.port
    else:
        return JsonResponse(
            {"status": "error", "message": "Router not found."}, status=404
        )

    # If custom is True, override the command with our fixed custom command.
    if custom_param:
        command = "show configuration | display set"
        print("Custom Command: running fixed command for log file download.")

    # Validate that the 'command' parameter is provided (unless overridden by custom).
    if not command:
        return JsonResponse(
            {
                "status": "error",
                "message": "The 'command' query parameter is required.",
            },
            status=400,
        )

    try:
        # Set up the SSH client and connect using the router's details
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=ROUTER_SSH_DETAILS["hostname"],
            port=ROUTER_SSH_DETAILS["port"],
            username=ROUTER_SSH_DETAILS["username"],
            password=ROUTER_SSH_DETAILS["password"],
        )
        channel = client.get_transport().open_session()
        channel.exec_command(command)
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Command failed: {e}"}, status=400
        )

    # --- Non-custom case: stream the command output ---
    if not custom_param:

        def stream_output():
            """Generator that yields output chunks every second, auto-closing after 20 seconds."""
            collected_output = ""
            yield f"STARTED QUERY AT {datetime.utcnow().strftime('%Y/%m/%d %H:%M:%S')} UTC\n"
            yield "Statistics from router:\n"

            start_time = time.time()  # Record the start time for timeout

            try:
                # Stream output while the command is running
                while True:
                    if channel.recv_ready():
                        chunk = channel.recv(1024).decode()
                        collected_output += chunk
                        yield chunk

                    if channel.exit_status_ready():
                        break

                    # If 20 seconds have passed, break out of the loop
                    if time.time() - start_time >= 20:
                        yield "\nTimeout reached (20 seconds). Closing connection...\n"
                        break

                    # Yield a newline to force a flush
                    yield "\n"
                    time.sleep(1)

                # Flush any remaining output
                while channel.recv_ready():
                    chunk = channel.recv(1024).decode()
                    collected_output += chunk
                    yield chunk
            except Exception as e:
                yield f"\nConnection aborted: {e}. Terminating SSH session.\n"
            finally:
                channel.close()
                client.close()

                # Save the command history for authenticated users.
                if request.user.is_authenticated:
                    output_data = collected_output.splitlines()
                    CommandHistory.objects.create(
                        user=request.user,
                        device=router,
                        command=command,
                        output=output_data,
                    )

        response = StreamingHttpResponse(stream_output(), content_type="text/plain")
        # Disable caching and (if behind nginx) disable its buffering
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    # --- Custom case: run custom command and return a downloadable log file ---
    else:
        collected_output = ""
        start_time = time.time()
        try:
            # Loop until the command finishes or a 20-second timeout is reached.
            while True:
                if channel.recv_ready():
                    chunk = channel.recv(1024).decode()
                    collected_output += chunk
                if channel.exit_status_ready():
                    break
                if time.time() - start_time >= 20:
                    collected_output += (
                        "\nTimeout reached (20 seconds). Closing connection...\n"
                    )
                    break
                time.sleep(1)
            # Flush any remaining output.
            while channel.recv_ready():
                chunk = channel.recv(1024).decode()
                collected_output += chunk
        except Exception as e:
            collected_output += f"\nConnection aborted: {e}. Terminating SSH session.\n"
        finally:
            channel.close()
            client.close()

            # Save the command history for authenticated users.
            if request.user.is_authenticated:
                output_data = collected_output.splitlines()
                CommandHistory.objects.create(
                    user=request.user,
                    device=router,
                    command=command,
                    output=output_data,
                )

        # Return the full output as a downloadable text file.
        response = HttpResponse(collected_output, content_type="text/plain")
        response["Content-Disposition"] = 'attachment; filename="router_config_log.txt"'
        return response

    return JsonResponse({"status": "error", "message": "Unexpected error."}, status=500)


@login_required(login_url="/login")
def dashboard(request):
    unique_cities = [
        f"{city}, {state}" if state else f"{city}"
        for city, state in DataCenter.objects.values_list("city", "state")
        .distinct()
        .order_by("city")
    ]
    categories = (
        Category.objects.prefetch_related("command_set")
        .filter(command__isnull=False)
        .distinct()
    )
    popular_commands = PopularCommand.objects.all()

    return render(
        request,
        "dashboard.html",
        {
            "unique_cities": unique_cities,
            "categories": categories,
            "popular_commands": popular_commands,
        },
    )


def get_devices_by_cities(request):
    if request.method == "GET":
        cities = request.GET.getlist("cities[]")  # Get the selected cities as a list
        city_names = [
            entry.split(",")[0] for entry in cities
        ]  # Extract only city names

        devices = Router.objects.filter(datacenter__city__in=city_names).values(
            "id", "name", "ip"
        )
        return JsonResponse({"devices": list(devices)})
    return JsonResponse({"error": "Invalid request method"}, status=400)

@login_required(login_url="/login")
def command_history_view(request):
    """
    View to display the command history for the logged-in user.
    """
    histories = CommandHistory.objects.filter(user=request.user).order_by("-timestamp")

    # Convert each history.output to JSON format
    formatted_histories = []
    for history in histories:
        try:
            output_data = json.loads(
                history.output
            )  # Try parsing JSON if already formatted
        except (json.JSONDecodeError, TypeError):
            output_data = history.output  # Use raw output if parsing fails

        truncated_output = format_html("<br>".join(output_data))[:100]
        if len(history.output) > 105:
            truncated_output += format_html("...")
            
        if history.device:
            device_name = history.device.name
        else:
            device_name = "No device hostname found!"

        formatted_histories.append(
            {
                "timestamp": history.timestamp,
                "device_name": device_name,
                "command": history.command,
                "output": json.dumps(output_data),  # Ensure it's a valid JSON string
                "truncated_output": truncated_output,
            }
        )

    return render(request, "command_history.html", {"histories": formatted_histories})
