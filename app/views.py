from django.shortcuts import get_object_or_404, render, redirect
from .models import (
    Alert,
    AlertRule,
    Category,
    CommandHistory,
    Configuration,
    DataCenter,
    PopularCommand,
    Router,
    SSHSettings,
)
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from datetime import datetime
from .utils import (
    execute_ssh_command,
    ROUTER_SSH_DETAILS,
    execute_ssh_command_while,
    ping_device_n_times,
    compare_and_return_changes,
    router_latencies,
    send_alert_email,
)
import time
import paramiko
from django.contrib.auth.decorators import login_required
from django.utils.html import format_html
import json
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_GET


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
            yield f"STARTED QUERY AT {datetime.now().strftime('%Y/%m/%d %I:%M:%S %p')} CST\n"
            yield "\n"

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
                    multiline_output = "\n".join(output_data)
                    CommandHistory.objects.create(
                        user=request.user,
                        device=router,
                        command=command,
                        output=multiline_output,
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
            # if request.user.is_authenticated:
            #     output_data = collected_output.splitlines()
            #     multiline_output = "\n".join(output_data)
            #     CommandHistory.objects.create(
            #         user=request.user,
            #         device=router,
            #         command=command,
            #         output=multiline_output
            #     )

        # Return the full output as a downloadable text file.
        response = HttpResponse(collected_output, content_type="text/plain")
        response["Content-Disposition"] = (
            f'attachment; filename="{router.name}_{router.ip}_configuration.txt"'
        )
        return response


@login_required(login_url="/login")
def dashboard2(request):
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

    return render(request, "dashboard.html")


def get_devices_by_datacenters(request):
    if request.method == "GET":
        cities = request.GET.getlist("cities[]")  # Get the selected cities as a list
        status = request.GET.get("status", "all")  # Get the status filter
        print(status, cities)

        # Build a list of datacenter info + their devices
        devices = []
        total_uptime_percentage = 0.0
        total_offline_devices = 0
        total_devices = 0

        # if cities contain 'all' then get cities from db
        if "all" in cities:
            cities = DataCenter.objects.all()

            for city in cities:
                city_devices_qs = Router.objects.filter(datacenter=city)
                if status != "all":
                    city_devices_qs = Router.objects.filter(
                        datacenter=city, status=status
                    )
                    print(city_devices_qs)
                # Build JSON-serializable list with property access
                devices_list = []
                for device in city_devices_qs:
                    latencies = router_latencies(device)
                    devices_list.append(
                        {
                            "id": device.id,
                            "ip": device.ip,
                            "name": device.name,
                            "status": device.status,
                            "latency": (
                                f"{device.avg_latency} ms"
                                if device.avg_latency
                                else "..."
                            ),
                            "uptime": (
                                f"{device.uptime_percentage}%"
                                if device.uptime_percentage
                                else "..."
                            ),
                            "latencies": latencies,
                            # "cpu_usage":  f'{device.cpu_usage}%' if device.cpu_usage else '...',
                            # "storage_usage": f'{device.storage_usage}%' if device.storage_usage else '...'
                        }
                    )
                    total_uptime_percentage += device.uptime_percentage
                    total_offline_devices += device.status == "offline"
                    total_devices += 1

                devices.append({"city": str(city), "devices": list(devices_list)})

            if total_devices > 0:
                total_uptime_percentage /= total_devices
                total_uptime_percentage = round(total_uptime_percentage, 2)
                total_uptime_percentage = f"{total_uptime_percentage}%"

            return JsonResponse(
                {
                    "status": "success",
                    "datacenters": devices,
                    "total_uptime_percentage": total_uptime_percentage,
                    "total_offline_devices": f"{total_offline_devices} Offline",
                    "total_devices": total_devices,
                }
            )

        # Otherwise, split city, state
        for city in cities:
            # Otherwise, split city, state
            try:
                try:
                    city_name, state = city.split(", ")
                except:
                    city_name, state, country = city.split(",")
            except:
                city_name = city
            city_devices_qs = Router.objects.filter(datacenter__city=city_name.strip())
            if status != "all":
                city_devices_qs = city_devices_qs.filter(status=status)
            # Build JSON-serializable list with property access
            devices_list = []
            for device in city_devices_qs:
                latencies = router_latencies(device)
                devices_list.append(
                    {
                        "id": device.id,
                        "ip": device.ip,
                        "name": device.name,
                        "status": device.status,
                        "latency": (
                            f"{device.avg_latency} ms" if device.avg_latency else "..."
                        ),
                        "uptime": (
                            f"{device.uptime_percentage}%"
                            if device.uptime_percentage
                            else "..."
                        ),
                        "latencies": latencies,
                        # "cpu_usage":  f'{device.cpu_usage}%' if device.cpu_usage else '...',
                        # "storage_usage": f'{device.storage_usage}%' if device.storage_usage else '...'
                    }
                )
                total_uptime_percentage += device.uptime_percentage
                total_offline_devices += device.status == "offline"
                total_devices += 1
            devices.append({"city": city, "devices": devices_list})

        if total_devices > 0:
            total_uptime_percentage /= total_devices
            total_uptime_percentage = round(total_uptime_percentage, 2)
            total_uptime_percentage = f"{total_uptime_percentage}%"

        return JsonResponse(
            {
                "status": "success",
                "datacenters": devices,
                "total_uptime_percentage": total_uptime_percentage,
                "total_offline_devices": f"{total_offline_devices} Offline",
                "total_devices": total_devices,
            }
        )

    return JsonResponse({"error": "Invalid request method"}, status=400)


def get_devices_by_cities(request):
    if request.method == "GET":
        cities = request.GET.getlist("cities[]")  # Get the selected cities as a list
        if len(cities):
            city_names = []
            for city in cities:
                # Extract only city names
                try:
                    try:
                        city_name, state = city.split(", ")
                    except:
                        city_name, state, country = city.split(",")
                except:
                    city_name = city
                city_names.append(city_name)
            devices = Router.objects.filter(datacenter__city__in=city_names).values(
                "id", "name", "ip"
            )
        else:
            city = request.GET.get("city", "")
            try:
                try:
                    city_name, state = city.split(", ")
                except:
                    city_name, state, country = city.split(",")
            except:
                city_name = city

            print(city_name)
            devices = Router.objects.filter(datacenter__city=city_name.strip()).values(
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
    formatted_histories = []

    for history in histories:
        # Try parsing history.output as JSON
        try:
            output_data = json.loads(history.output)
        except (json.JSONDecodeError, TypeError):
            output_data = history.output  # Fall back to the raw output

        # If output_data is a list, join its elements with <br>
        if isinstance(output_data, list):
            # Escape each line to ensure safety and join with <br>
            joined_output = mark_safe("<br>".join(escape(line) for line in output_data))
        else:
            # If it's not a list, treat it as a string
            joined_output = escape(output_data)

        # Use a placeholder in format_html to avoid formatting issues with curly braces
        truncated_output = format_html("{}", joined_output)[:100]
        if len(joined_output) > 105:
            truncated_output += "..."

        # Get device name or a default message
        device_name = (
            history.device.name if history.device else "No device hostname found!"
        )

        formatted_histories.append(
            {
                "timestamp": history.timestamp,
                "device_name": device_name,
                "command": history.command,
                "output": json.dumps(output_data),  # Ensure a valid JSON string
                "truncated_output": truncated_output,
            }
        )

    return render(request, "command_history.html", {"histories": formatted_histories})


import json


@require_GET
def download_configuration(request):
    selected_devices_str = request.GET.get("selectedDevices", "[]")
    selected_devices = json.loads(selected_devices_str)  # list of {id, name, ip, ...}

    # Example: build a dict of device.id -> [lines of config]
    configuration_data = {}
    for dev in selected_devices:
        device_id = dev["id"]
        device_ip = dev["ip"]
        try:
            output = execute_ssh_command_while(
                "show configuration | display set",
                hostname=device_ip,
                delay_in_seconds=5,
            )
        except:
            output = "0"
        configuration_data[device_id] = device_ip + "\n" + output

    return JsonResponse({"configuration": configuration_data})


from django.utils.dateformat import DateFormat
from django.db.models import Sum, Count, Case, When, IntegerField


def temp(request):
    return render(request, "temp/base.html")


@login_required(login_url="/login")
def dashboard(request):
    datacenters = DataCenter.objects.all()

    devices = list(Router.objects.all())
    total_devices = len(devices)
    offline_devices = sum(device.status == "offline" for device in devices)
    network_uptime = (
        (sum(device.uptime_percentage for device in devices) / total_devices)
        if total_devices
        else 0
    )
    active_alerts = "..."

    alerts = Alert.objects.order_by("-created_at")[:5]

    context = {
        "total_devices": total_devices,
        "offline_devices": offline_devices,
        "network_uptime": f"{int(network_uptime)}%",
        "active_alerts": active_alerts,
        "datacenters": datacenters,
        "alerts": alerts,
    }

    return render(request, "temp/dashboard.html", context)


@login_required(login_url="/login")
def history(request):
    histories = (
        CommandHistory.objects.filter(user=request.user)
        .select_related("device")  # so we can access device fields efficiently
        .order_by("-timestamp")
    )

    data = []
    for h in histories:
        # Format the timestamp however you like:
        # e.g. YYYY-MM-DD HH:MM:SS or using strftime
        formatted_ts = DateFormat(h.timestamp).format("Y-m-d H:i:s")

        data.append(
            {
                "id": h.id,
                "device_name": h.device.name if h.device else "No Device",
                "command": h.command,
                "timestamp": formatted_ts,
                "output": h.output,
            }
        )

    return JsonResponse(
        {
            "status": "success",
            "data": data,
        }
    )


@login_required(login_url="/login")
def devices(request):
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
        .order_by("order")
    )
    popular_commands = PopularCommand.objects.all()
    context = {
        "title": "Devices",
        "unique_cities": unique_cities,
        "categories": categories,
        "popular_commands": popular_commands,
    }
    return render(request, "temp/devices.html", context)


@login_required(login_url="/login")
def monitoring(request):
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
    context = {
        "title": "Monitoring",
        "unique_cities": unique_cities,
        "categories": categories,
        "popular_commands": popular_commands,
    }
    return render(request, "temp/monitoring.html", context)


import os
from django.shortcuts import render


def rsyslog_log_view(request):
    base_log_dir = "/var/log/syslog_logs"
    log_entries = []
    threshold = time.time() - (30 * 24 * 60 * 60)  # 30 days ago

    # Ensure the base log directory exists
    if os.path.exists(base_log_dir):
        # Iterate over each device folder (device name)
        for device in os.listdir(base_log_dir):
            if device == "net-tools":
                continue
            device_path = os.path.join(base_log_dir, device)
            if os.path.isdir(device_path):
                # Iterate over each file in the device folder
                for log_file in os.listdir(device_path):
                    file_path = os.path.join(device_path, log_file)
                    if os.path.isfile(file_path):
                        # Skip files older than 30 days:
                        if os.path.getmtime(file_path) < threshold:
                            continue
                        try:
                            with open(file_path, "r") as f:
                                for line in f:
                                    line = line.strip()
                                    if not line:
                                        continue  # Skip empty lines
                                    # Assume the first token is the timestamp
                                    parts = line.split()
                                    timestamp_str = parts[0] if parts else "N/A"
                                    # Format the timestamp if possible
                                    try:

                                        dt = datetime.fromisoformat(
                                            timestamp_str.replace("Z", "+00:00")
                                        )
                                        formatted_time = dt.strftime(
                                            "%Y-%m-%d %I:%M:%S %p"
                                        )
                                    except ValueError:
                                        # If timestamp parsing fails, use the original string
                                        formatted_time = timestamp_str
                                    message = (
                                        " ".join(parts[1:]) if len(parts) > 1 else ""
                                    )
                                    log_entries.append(
                                        {
                                            "timestamp": formatted_time,
                                            "device": device,
                                            "source": log_file.replace(
                                                ".log", ""
                                            ).upper(),
                                            "message": message,
                                        }
                                    )
                        except Exception as e:
                            log_entries.append(
                                {
                                    "timestamp": "Error",
                                    "device": device,
                                    "source": log_file,
                                    "message": f"Failed to read file: {str(e)}",
                                }
                            )

    # sort the log entries by timestamp (assumes "YYYY-MM-DD HH:MM:SS" format)
    # log_entries.sort(key=lambda entry: entry['timestamp'], reverse=True)
    context = {"log_entries": log_entries, "title": "Syslog"}
    return render(request, "temp/syslog.html", context)


def delete_alert_rule(request):
    if request.method == "POST":
        alert_id = request.POST.get("id")
        try:
            alert_rule = AlertRule.objects.get(id=alert_id)
            alert_rule.delete()
            return JsonResponse({"status": "success", "id": alert_rule.id})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


def create_alert_rule(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        type_value = request.POST.get("type")
        syslog_strings = request.POST.get("syslog_strings", "")
        if type_value != "SYSLOG":
            syslog_strings = ""

        # Create the AlertRule object
        alert_rule = AlertRule.objects.create(
            name=name,
            description=description,
            type=type_value,  # Assuming the value matches one of the model's choices
            syslog_strings=syslog_strings,
        )

        return JsonResponse({"status": "success", "id": alert_rule.id})
    else:
        return JsonResponse(
            {"status": "error", "message": "Invalid request method."}, status=400
        )


def configuration_view(request):
    requestType = request.GET.get("requestType")
    if requestType == "getCompareFiles":
        selected_ids = request.GET.getlist("ids[]", [])
        if len(selected_ids) != 2:
            return JsonResponse(
                {
                    "error": "Please select exactly two configuration files for comparison."
                },
                status=400,
            )
        configs = Configuration.objects.filter(id__in=selected_ids)
        if configs.count() != 2:
            return JsonResponse(
                {"error": "One or more configuration files could not be found."},
                status=404,
            )
        file1_path = configs[0].file.path
        file2_path = configs[1].file.path
        changes_file1, changes_file2 = compare_and_return_changes(
            file1_path, file2_path
        )

        return JsonResponse(
            {
                "message": "Comparison completed successfully.",
                "selected_ids": selected_ids,
                "changes_file1": changes_file1,
                "changes_file2": changes_file2,
            }
        )
    if requestType == "getConfigurations":
        device_id = request.GET.get("device_id")
        configs = list(
            Configuration.objects.filter(router__id=device_id).values(
                "id", "router__name", "router__ip", "version", "created_at", "file"
            )
        )
        return JsonResponse({"configs": configs})

    unique_cities = [
        f"{city}, {state}" if state else f"{city}"
        for city, state in DataCenter.objects.values_list("city", "state")
        .distinct()
        .order_by("city")
    ]
    context = {
        "unique_cities": unique_cities,
        "title": "Configuration",
        "conf_data": [],
    }

    return render(request, "temp/configuration.html", context)


def alerts_view(request):
    alerts = AlertRule.objects.all()  # Retrieve all alert rules
    context = {"title": "Alerts", "alerts": alerts}
    return render(request, "temp/alerts.html", context)


from django.views.decorators.csrf import csrf_exempt
import re


@csrf_exempt
def check_syslog_view(request):
    if request.method == "POST":
        try:
            # Decode and load the JSON payload from the request body.
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload"}, status=400)
        # Expecting the payload to contain an "alerts" key.
        alerts = data.get("alerts")
        if alerts is None:
            return JsonResponse({"error": "No alerts provided"}, status=400)

        # Process alerts here. For example, you might log each one or perform further processing.
        for alert in alerts:
            # Extract fields with default values if not provided.
            hostname = alert.get("hostname", "Unknown")
            program = alert.get("program", "Unknown")
            msg = alert.get("msg", "")
            rule_names = alert.get("matched_rule_names", [])
            rule_names_str = (', ').join(rule_names)
            # Log the alert details; replace this with your processing logic.
            print(f"Received alert [{rule_names_str}] from {hostname} ({program}): {msg}")

        if hostname == "net-tools":
            return JsonResponse(
                {"error": "Invalid request, 'Same Hostname'"}, status=400
            )

        # Define keywords as a comma-separated string
        keywords_str = "BGP, OSPF, RPD, ISIS, MPLS"
        keywords = [kw.strip() for kw in keywords_str.split(",")]
        pattern = re.compile("|".join(keywords), re.IGNORECASE)

        # Find all matching keywords in the alert message
        # matching_keywords = pattern.findall(msg)

        if msg and hostname != "net-tools":
            email_subject = f"{rule_names_str} ({program}): {hostname}"
            # Using set() to list each matching keyword only once
            email_body = (
                # f"The following keywords were found in the alert message: {', '.join(set(matching_keywords))}\n\n"
                f"{msg}"
            )

            # Send the email (customize from_email and recipient_list as needed in send_alert_email)
            send_alert_email(
                alert_type="SYSLOG",
                subject=email_subject,
                message=email_body,
                hostname=hostname,
                program=program,
            )

            return JsonResponse({"status": "success", "alert": msg})
        else:
            return JsonResponse({"status": "no matching keywords found", "alert": msg})
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)
