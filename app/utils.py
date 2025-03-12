from datetime import timedelta
import subprocess
import paramiko
import time
import re

from app.models import Latency, Router

# Router SSH Details
ROUTER_SSH_DETAILS = {
    "hostname": "23.141.136.2",
    "port": 22,
    "username": "txfiber",
    "password": "southtx956",
}


def execute_ssh_command(
    command,
    command2=None,
    hostname=ROUTER_SSH_DETAILS["hostname"],
    delay_in_seconds=None,
):
    """
    Execute a command on the router via SSH and return the output.
    If wait is True, continuously read the output until the command completes.
    """
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=hostname,
            port=ROUTER_SSH_DETAILS["port"],
            username=ROUTER_SSH_DETAILS["username"],
            password=ROUTER_SSH_DETAILS["password"],
        )

        if command2:
            combined_cmd = f"{command}; echo '----SPLIT----'; {command2}"
        else:
            combined_cmd = command

        # Execute the traceroute command
        channel = client.get_transport().open_session()
        channel.exec_command(combined_cmd)

        # Wait
        if delay_in_seconds:
            time.sleep(delay_in_seconds)

        output = channel.recv(65535).decode()  # Get remaining output

        channel.close()
        client.close()

        return output

    except Exception as e:
        raise Exception(f"SSH command execution failed: {e}")


def execute_ssh_command_while(
    command, hostname=ROUTER_SSH_DETAILS["hostname"], delay_in_seconds=None
):
    """
    Execute a command on the router via SSH and return the output.
    If wait is True, continuously read the output until the command completes.
    """
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=hostname,
            port=ROUTER_SSH_DETAILS["port"],
            username=ROUTER_SSH_DETAILS["username"],
            password=ROUTER_SSH_DETAILS["password"],
        )

        # Execute the traceroute command
        channel = client.get_transport().open_session()
        channel.exec_command(command)

        collected_output = ""

        start_time = time.time()  # Record the start time for timeout

        try:
            # Stream output while the command is running
            while True:
                if channel.recv_ready():
                    chunk = channel.recv(1024).decode()
                    collected_output += chunk

                if channel.exit_status_ready():
                    break

                # If delay seconds have passed, break out of the loop
                if time.time() - start_time >= delay_in_seconds:
                    break

                time.sleep(1)

            # Flush any remaining output
            while channel.recv_ready():
                chunk = channel.recv(1024).decode()
                collected_output += chunk
        except Exception as e:
            print(f"Connection aborted: {e}. Terminating SSH session.")
        finally:
            channel.close()
            client.close()

        return collected_output

    except Exception as e:
        raise Exception(f"SSH command execution failed: {e}")


def ping_device_once(ip_address):
    """
    Returns True if single ping is successful, False otherwise.
    """
    try:
        # Example (Linux/Mac): "-c 1" => 1 ICMP request, "-W 1" => 1-second timeout
        # for windows use "-n 1" instead of "-c 1"
        output = subprocess.check_output(
            ["ping", "-c", "1", "-w", "1", ip_address], stderr=subprocess.STDOUT
        ).decode("utf-8")
        # Attempt to extract the average latency from the rtt summary line.
        # Example line: "rtt min/avg/max/mdev = 7.963/7.963/7.963/0.000 ms"
        match = re.search(
            r"rtt min/avg/max/mdev = [\d\.]+/([\d\.]+)/[\d\.]+/[\d\.]+ ms", output
        )
        if match:
            avg_latency = float(match.group(1))
        else:
            # Fallback: extract latency from the reply line: "time=7.96 ms"
            match = re.search(r"time=([\d\.]+) ms", output)
            avg_latency = float(match.group(1)) if match else None

        return True, avg_latency
    except subprocess.CalledProcessError:
        return False, None


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
    avg_latency = 0.0
    for _ in range(count):
        success, latency = ping_device_once(ip_address)
        if success:
            successes += 1
            avg_latency += latency

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

    avg_latency = round(avg_latency / successes, 2)

    return {
        "successes": successes,
        "failures": failures,
        "status": status,
        "avg_latency": avg_latency,
    }


def get_device_stats(device_id=78):
    """
    GET /get_device_stats?device_id=123
    Returns JSON with {status, cpu, storage} for the device,
    determined by 3 consecutive pings in a single request.
    """
    device = Router.objects.filter(id=device_id).first()
    if not device:
        return {"error": f"{device_id} device not found"}

    # Ping 3 times in one shot
    ping_results = ping_device_n_times(device.ip, count=3)
    status = ping_results["status"]
    failures = ping_results["failures"]
    successes = ping_results["successes"]
    avg_latency = ping_results["avg_latency"]

    # Fake CPU & storage usage or retrieve real data from your source
    cpu_usage = 50
    overall_storage_usage = 80

    # Get CPU and memory usage from the device
    # cpu_usage, mem_usage = get_cpu_and_mem(device.ip)
    # filesystems_usage, overall_storage_usage = get_storage(device.ip)

    return {
        "status": "success",
        "stats": {
            "status": status,
            "cpu": "...",
            "storage": "...",
            "successes": successes,
            "failures": failures,
            "avg_latency": avg_latency,
        },
    }


def install_package_if_missing(command):
    """
    Check if a package is missing and install it via SSH.
    """
    try:
        install_command = f"which {command.split()[0]} || sudo apt-get install -y {command.split()[0]}"
        return execute_ssh_command(install_command)
    except Exception as e:
        raise Exception(f"Failed to install missing package: {e}")


def convert_to_bytes(size_str):
    """
    Convert a string like '10.0G', '952M', '236K' to an integer byte value.
    Assumes G=Gigabytes, M=Megabytes, K=Kilobytes.
    """
    size_str = size_str.strip().upper()
    # Regex to match something like "10.0G" or "952M" or "76K"
    match = re.match(r"([\d\.]+)([GMK])", size_str)
    if not match:
        # If no unit, or doesn't match, assume it's bytes
        # or return 0 to skip
        try:
            return int(size_str)
        except ValueError:
            return 0

    value, unit = match.groups()
    value = float(value)

    if unit == "G":
        return int(value * 1024 * 1024 * 1024)
    elif unit == "M":
        return int(value * 1024 * 1024)
    elif unit == "K":
        return int(value * 1024)
    return int(value)


def parse_junos_storage(output):
    """
    Parses 'show system storage' output, returns:
      - A list of filesystem info: [
          {
            'filesystem': '/dev/gpt/junos',
            'size_str': '10.0G',
            'used_str': '2.2G',
            'avail_str': '7.0G',
            'capacity_str': '24%',
            'mount': '/.mount',
            'size_bytes': 10737418240,
            'used_bytes': 2362232012,
            'capacity_pct': 24
          },
          ...
        ]
      - Overall usage across all filesystems (used_bytes / size_bytes * 100)
        (this is only meaningful if you want a grand total)
    """
    lines = output
    # Find the header line (starts with "Filesystem") so we know where to begin parsing
    header_index = None
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("filesystem"):
            header_index = i
            break
    if header_index is None:
        return [], 0.0  # No valid header found

    # The actual data lines follow the header
    data_lines = lines[header_index + 1 :]

    filesystems = []
    total_size_bytes = 0
    total_used_bytes = 0

    for line in data_lines:
        line = line.strip()
        if not line:
            continue  # skip blank lines

        # Split by whitespace
        parts = line.split()
        # We expect at least 6 columns: Filesystem, Size, Used, Avail, Capacity, Mounted on
        if len(parts) < 6:
            continue

        fs = parts[0]
        size_str = parts[1]
        used_str = parts[2]
        avail_str = parts[3]
        capacity_str = parts[4]
        # The rest of the parts might be the mount path (sometimes it's one part, sometimes multiple)
        mount_on = " ".join(parts[5:])

        size_bytes = convert_to_bytes(size_str)
        used_bytes = convert_to_bytes(used_str)

        # capacity_str is something like "24%"
        match = re.match(r"(\d+)%", capacity_str)
        capacity_pct = int(match.group(1)) if match else 0

        filesystems.append(
            {
                "filesystem": fs,
                "size_str": size_str,
                "used_str": used_str,
                "avail_str": avail_str,
                "capacity_str": capacity_str,
                "mount": mount_on,
                "size_bytes": size_bytes,
                "used_bytes": used_bytes,
                "capacity_pct": capacity_pct,
            }
        )

        # Accumulate totals
        total_size_bytes += size_bytes
        total_used_bytes += used_bytes

    # Calculate overall usage percentage
    overall_usage_pct = 0.0
    if total_size_bytes > 0:
        overall_usage_pct = (total_used_bytes / total_size_bytes) * 100.0
    # round to 2 decimal places
    overall_usage_pct = round(overall_usage_pct, 2)

    return filesystems, overall_usage_pct


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
        # Look for something like "99.0% idle upto 2 decimal places"
        match = re.search(r"(\d+(\.\d+)?)%\s+idle", cpu_line)
        if match:
            idle_val = float(match.group(1))
            cpu_usage = 100.0 - idle_val  # total usage
            cpu_usage = round(cpu_usage, 2)

    # 3) Parse the Mem line => parse each field (Active, Inact, Wired, Buf, Free)
    mem_usage = None
    if mem_line:
        # Example: Mem: 353M Active, 4621M Inact, 947M Wired, 300M Buf, 10G Free
        # We'll capture the numeric portion + unit for each label
        active_match = re.search(r"(\S+)\s+Active", mem_line)
        inact_match = re.search(r"(\S+)\s+Inact", mem_line)
        wired_match = re.search(r"(\S+)\s+Wired", mem_line)
        buf_match = re.search(r"(\S+)\s+Buf", mem_line)
        free_match = re.search(r"(\S+)\s+Free", mem_line)

        if all([active_match, inact_match, wired_match, buf_match, free_match]):
            # Convert "353M" -> float MB, "10G" -> float MB, etc.
            def to_mb(s):
                # e.g. "353M" => 353.0, "10G" => 10240.0
                unit = s[-1].upper()
                val = float(s[:-1])
                if unit == "M":
                    return val
                elif unit == "G":
                    return val * 1024
                return val  # fallback if no unit, e.g. "512"

            active_val = to_mb(active_match.group(1))
            inact_val = to_mb(inact_match.group(1))
            wired_val = to_mb(wired_match.group(1))
            buf_val = to_mb(buf_match.group(1))
            free_val = to_mb(free_match.group(1))

            total = active_val + inact_val + wired_val + buf_val + free_val
            used = total - free_val

            if total > 0:
                mem_usage = (used / total) * 100.0

    return cpu_usage, mem_usage


def get_cpu_and_mem(device_ip="23.141.136.2"):
    # command to get cpu and memory usage, using ssh into that device 'show system processes extensive'

    # ssh into the device and get the output
    output = execute_ssh_command(
        "show system processes extensive | match nice", hostname=device_ip
    )

    # Parse the output to get CPU and memory usage
    cpu_usage, mem_usage = parse_show_system_processes_extensive(output.splitlines())

    return cpu_usage, mem_usage


def get_storage(device_ip="23.141.136.2"):
    # command to get storage usage, using ssh into that device 'show system storage'

    # ssh into the device and get the output
    output = execute_ssh_command("show system storage", hostname=device_ip)

    # Parse the output to get storage usage
    filesystems, overall_usage_pct = parse_junos_storage(output.splitlines())

    return filesystems, overall_usage_pct


def get_device_stats(device_ip="23.141.136.2"):
    # Get CPU, memory, storage usage of the device
    output = execute_ssh_command(
        "show system processes extensive | match nice",
        "show system storage",
        hostname=device_ip,
    )
    print(output)
    # split the output into two parts
    cpu_output = []
    storage_output = []
    split = False
    for line in output.splitlines():
        if line.strip() == "----SPLIT----":
            split = True
            continue
        if not split:
            cpu_output.append(line)
        else:
            storage_output.append(line)
    print(22, storage_output)

    # Parse the output to get CPU and memory usage
    cpu_usage, mem_usage = parse_show_system_processes_extensive(cpu_output)

    # Parse the output to get storage usage
    _, overall_storage_pct = parse_junos_storage(storage_output)

    return cpu_usage, mem_usage, overall_storage_pct


def compare_and_return_changes(file1_path, file2_path):
    # # Example usage:
    # file1 = "path/to/file1.txt"
    # file2 = "path/to/file2.txt"

    # changes_file1, changes_file2 = compare_and_return_changes(file1, file2)

    # print("Lines that differ in File1:")
    # for line in changes_file1:
    #     print(repr(line))

    # print("\nLines that differ in File2:")
    # for line in changes_file2:
    #     print(repr(line))

    with open(file1_path, "r", encoding="utf-8") as f1, open(
        file2_path, "r", encoding="utf-8"
    ) as f2:
        lines1 = f1.readlines()
        lines2 = f2.readlines()

    max_len = max(len(lines1), len(lines2))

    changed_lines_file1 = []
    changed_lines_file2 = []

    for i in range(max_len):
        line1 = lines1[i].rstrip("\n") if i < len(lines1) else None
        line2 = lines2[i].rstrip("\n") if i < len(lines2) else None

        if line1 != line2:
            changed_lines_file1.append(line1)
            changed_lines_file2.append(line2)

    return changed_lines_file1, changed_lines_file2


from django.utils import timezone
from django.db.models.functions import TruncHour
from django.db.models import Avg


def router_latencies(router):
    # 1) The cutoff time
    now = timezone.now()
    cutoff = now - timedelta(hours=24)

    # 2) Build a list of hourly datetimes from cutoff to now
    #    We'll store them in ascending order
    hours_list = []
    current = cutoff.replace(minute=0, second=0, microsecond=0)
    while current <= now:
        hours_list.append(current)
        current += timedelta(hours=1)

    # 3) Query existing data grouped by truncated hour
    hourly_data_qs = (
        Latency.objects.filter(router=router, created_at__gte=cutoff)
        .annotate(hour=TruncHour("created_at"))
        .values("hour")
        .annotate(avg_latency=Avg("latency"))
        .order_by("hour")
    )

    # 4) Convert QuerySet to a dict keyed by the truncated hour, with the avg latency
    data_dict = {}
    for rec in hourly_data_qs:
        # rec['hour'] is a datetime truncated to the hour
        # rec['avg_latency'] is the average for that hour
        data_dict[rec["hour"]] = rec["avg_latency"]

    # 5) Merge results:
    #    For each hour in hours_list, check if we have data in data_dict.
    #    If not, set None.
    final_results = []
    for hour_dt in hours_list:
        avg_val = data_dict.get(hour_dt, None)
        if avg_val:
            avg_val = round(avg_val, 2)
        final_results.append(
            {
                "hour": hour_dt,
                "avg_latency": avg_val,
            }
        )

    return final_results
