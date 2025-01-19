import paramiko
import time

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
        time.sleep(delay_in_seconds)

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
