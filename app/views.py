import subprocess
from django.shortcuts import get_object_or_404, render, redirect
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
    
    print("Router ID: ", router_id)
    print("Command: ", command)

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
                        output=multiline_output
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

    return render(
        request,
        "dashboard.html",
        {
            "unique_cities": unique_cities,
            "categories": categories,
            "popular_commands": popular_commands,
        },
    )


def ping_device_once(ip_address):
    """
    Returns True if single ping is successful, False otherwise.
    """
    try:
        # Example (Linux/Mac): "-c 1" => 1 ICMP request, "-W 1" => 1-second timeout
        # for windows use "-n 1" instead of "-c 1"
        subprocess.check_output(
            ["ping", "-c", "1", "-w", "1", ip_address],
            stderr=subprocess.STDOUT
        )
        return True
    except subprocess.CalledProcessError:
        return False

def ping_device_n_times(ip_address, count=3):
    """
    Pings the device `count` times, returns:
      {
        "successes": int,
        "failures": int,
        "status": "online"/"warning"/"offline"
      }
    """
    successes = 0
    for _ in range(count):
        if ping_device_once(ip_address):
            successes += 1

    failures = count - successes

    # Determine status based on successes/failures
    if successes == 0:
        # All pings failed
        status = "offline"
    elif successes < count:
        # Some pings failed, some succeeded
        status = "warning"
    else:
        # All pings succeeded
        status = "online"

    return {
        "successes": successes,
        "failures": failures,
        "status": status
    }

def parse_show_system_processes_extensive(output):
    """
    Parses lines like:
      CPU:  0.7% user,  0.0% nice,  0.3% system,  0.1% interrupt, 99.0% idle
      Mem: 353M Active, 4621M Inact, 947M Wired, 300M Buf, 10G Free
    Returns (cpu_usage_percent, mem_usage_percent) as floats or None if not found.
    """

    cpu_line = None
    mem_line = None

    # 1) Identify the lines we need
    for line in output:
        line = line.strip()
        if line.startswith("CPU:"):
            cpu_line = line
        elif line.startswith("Mem:"):
            mem_line = line

    # 2) Parse the CPU line => total usage = 100% - idle%
    cpu_usage = None
    if cpu_line:
        # Look for something like "99.0% idle"
        match = re.search(r'(\d+(\.\d+)?)%\s+idle', cpu_line)
        if match:
            idle_val = float(match.group(1))
            cpu_usage = 100.0 - idle_val  # total usage

    # 3) Parse the Mem line => parse each field (Active, Inact, Wired, Buf, Free)
    mem_usage = None
    if mem_line:
        # Example: Mem: 353M Active, 4621M Inact, 947M Wired, 300M Buf, 10G Free
        # We'll capture the numeric portion + unit for each label
        active_match = re.search(r'(\S+)\s+Active', mem_line)
        inact_match = re.search(r'(\S+)\s+Inact', mem_line)
        wired_match = re.search(r'(\S+)\s+Wired', mem_line)
        buf_match   = re.search(r'(\S+)\s+Buf',   mem_line)
        free_match  = re.search(r'(\S+)\s+Free',  mem_line)

        if all([active_match, inact_match, wired_match, buf_match, free_match]):
            # Convert "353M" -> float MB, "10G" -> float MB, etc.
            def to_mb(s):
                # e.g. "353M" => 353.0, "10G" => 10240.0
                unit = s[-1].upper()
                val = float(s[:-1])
                if unit == 'M':
                    return val
                elif unit == 'G':
                    return val * 1024
                return val  # fallback if no unit, e.g. "512"

            active_val = to_mb(active_match.group(1))
            inact_val  = to_mb(inact_match.group(1))
            wired_val  = to_mb(wired_match.group(1))
            buf_val    = to_mb(buf_match.group(1))
            free_val   = to_mb(free_match.group(1))

            total = active_val + inact_val + wired_val + buf_val + free_val
            used  = total - free_val

            if total > 0:
                mem_usage = (used / total) * 100.0

    return cpu_usage, mem_usage

def get_cpu_and_mem(device_ip):
    # command to get cpu and memory usage, using ssh into that device 'show system processes extensive'

    try:
        # ssh into the device and get the output    
        output = execute_ssh_command("show system processes extensive", hostname=device_ip)
        
        # Parse the output to get CPU and memory usage
        cpu_usage, mem_usage = parse_show_system_processes_extensive(output)
    except Exception as e:
        # Log the error and return None for both values
        print(f"Error getting CPU and memory usage: {e}")
        cpu_usage = mem_usage = 0
    
    return cpu_usage, mem_usage
    
    
    
    
    
    
@require_GET
def get_device_stats(request, device_id=78):
    """
    GET /get_device_stats?device_id=123
    Returns JSON with {status, cpu, storage} for the device,
    determined by 3 consecutive pings in a single request.
    """
    device = Router.objects.filter(id=device_id).first()
    if not device:
        return JsonResponse({"error": f"{device_id} device not found"}, status=404)

    # Ping 3 times in one shot
    ping_results = ping_device_n_times(device.ip, count=3)
    status = ping_results["status"]
    failures = ping_results["failures"]
    successes = ping_results["successes"]

    # Fake CPU & storage usage or retrieve real data from your source
    cpu_usage = 50
    storage_usage = 80
    
    # Get CPU and memory usage from the device
    cpu_usage, mem_usage = get_cpu_and_mem(device.ip)

    return JsonResponse({
        "status": "success",
        "stats": {
            "status": status,
            "cpu": cpu_usage,
            "storage": storage_usage,
            "successes": successes,
            "failures": failures
        }
    })

def get_devices_by_datacenters(request):
    if request.method == "GET":
        cities = request.GET.getlist("cities[]")  # Get the selected cities as a list
        
        # Build a list of datacenter info + their devices
        devices = []
        
        # if cities contain 'all' then get cities from db 
        if 'all' in cities:
            cities = DataCenter.objects.all()
            for city in cities:
                city_devices = (
                    Router.objects.filter(datacenter=city)
                    .values("id", "name", "ip")
                )
                devices.append({"city": str(city),
                                "devices": list(city_devices)})
            return JsonResponse({"status": "success", "datacenters": devices})
        
        
        # Otherwise, split city, state        
        for city in cities:
            # Otherwise, split city, state
            city_name, state = city.split(",")
            city_devices = (
                Router.objects.filter(datacenter__city=city_name.strip())
                .values("id", "name", "ip")
            )
            devices.append({"city": city, "devices": list(city_devices)})
            
        return JsonResponse({"status": "success", "datacenters": devices})
        
    return JsonResponse({"error": "Invalid request method"}, status=400)


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

from django.utils.dateformat import DateFormat


def temp(request):
    return render(request, "temp/base.html")

def dashboard(request):
    context = {'title': 'Dashboard'}
    return render(request, "temp/dashboard.html", context)

@login_required(login_url="/login")
def history(request):
    histories = (
        CommandHistory.objects
        .filter(user=request.user)
        .select_related("device")      # so we can access device fields efficiently
        .order_by("-timestamp")
    )

    data = []
    for h in histories:
        # Format the timestamp however you like:
        # e.g. YYYY-MM-DD HH:MM:SS or using strftime
        formatted_ts = DateFormat(h.timestamp).format("Y-m-d H:i:s")

        data.append({
            "id": h.id,
            "device_name": h.device.name if h.device else "No Device",
            "command": h.command,
            "timestamp": formatted_ts,
            "output": h.output,
        })

    return JsonResponse({
        "status": "success",
        "data": data,
    })

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
    )
    popular_commands = PopularCommand.objects.all()
    context = {
            'title': 'Devices',
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
            'title': 'Monitoring',
            "unique_cities": unique_cities,
            "categories": categories,
            "popular_commands": popular_commands,
        }
    return render(request, "temp/monitoring.html", context)
