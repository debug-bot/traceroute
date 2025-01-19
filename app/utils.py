import paramiko


# Router SSH Details
ROUTER_SSH_DETAILS = {
    "hostname": "23.141.136.2",
    "port": 22,
    "username": "txfiber",
    "password": "southtx956",
}


def execute_ssh_command(command, wait=True):
    """
    Execute a command on the router via SSH and return the output.
    If wait is True, continuously read the output until the command completes.
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

        output_lines = []
        if wait:
            # Read output in real-time
            while not stdout.channel.exit_status_ready():
                if stdout.channel.recv_ready():
                    output = stdout.channel.recv(1024).decode()  # Read in chunks
                    output_lines.extend(output.splitlines())

        # Finalize reading after the command completes
        output = stdout.read().decode()
        output_lines.extend(output.splitlines())

        error = stderr.read().decode()
        client.close()

        if error:
            raise Exception(error)

        return output_lines

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
