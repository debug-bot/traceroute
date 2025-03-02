import paramiko
import time
import re

# Router SSH Details
ROUTER_SSH_DETAILS = {
    "hostname": "23.141.136.2",
    "port": 22,
    "username": "txfiber",
    "password": "southtx956",
}


def execute_ssh_command(command, hostname=ROUTER_SSH_DETAILS["hostname"], delay_in_seconds=20):
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
        
        # Wait
        # time.sleep(delay_in_seconds)

        output = channel.recv(65535).decode()  # Get remaining output

        data = output.splitlines()
        
        channel.close()
        client.close()
        
        

        return data

    except Exception as e:
        raise Exception(f"SSH command execution failed: {e}")


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

    if unit == 'G':
        return int(value * 1024 * 1024 * 1024)
    elif unit == 'M':
        return int(value * 1024 * 1024)
    elif unit == 'K':
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
    data_lines = lines[header_index+1:]

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

        filesystems.append({
            "filesystem": fs,
            "size_str": size_str,
            "used_str": used_str,
            "avail_str": avail_str,
            "capacity_str": capacity_str,
            "mount": mount_on,
            "size_bytes": size_bytes,
            "used_bytes": used_bytes,
            "capacity_pct": capacity_pct
        })

        # Accumulate totals
        total_size_bytes += size_bytes
        total_used_bytes += used_bytes

    # Calculate overall usage percentage
    overall_usage_pct = 0.0
    if total_size_bytes > 0:
        overall_usage_pct = (total_used_bytes / total_size_bytes) * 100

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

def get_cpu_and_mem(device_ip='23.141.136.2'):
    # command to get cpu and memory usage, using ssh into that device 'show system processes extensive'

    try:
        # ssh into the device and get the output    
        output = execute_ssh_command("show system processes extensive | match nice", hostname=device_ip)
        
        # Parse the output to get CPU and memory usage
        cpu_usage, mem_usage = parse_show_system_processes_extensive(output)
    except Exception as e:
        # Log the error and return None for both values
        print(f"Error getting CPU and memory usage: {e}")
        cpu_usage = mem_usage = 0
    
    return cpu_usage, mem_usage
    
def get_storage(device_ip='23.141.136.2'):
    # command to get storage usage, using ssh into that device 'show system storage'

    try:
        # ssh into the device and get the output    
        output = execute_ssh_command("show system storage", hostname=device_ip)
        
        # Parse the output to get storage usage
        filesystems, overall_usage_pct = parse_junos_storage(output)
    except Exception as e:
        # Log the error and return None for both values
        print(f"Error getting storage usage: {e}")
        filesystems = overall_usage_pct = 0
    
    return filesystems, overall_usage_pct