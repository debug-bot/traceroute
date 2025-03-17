#!/home/txfiber/traceroute/venv/bin/python
import sys
import select
import time
import requests
import json
import re

DEBUG_LOG = "/var/log/rsyslog_wrapper/check_syslog_wrapper_debug.log"
POST_URL = "https://fastcli.com/check-syslog/"
AGGREGATION_TIMEOUT = 2  # seconds


def log_debug(message):
    try:
        with open(DEBUG_LOG, "a") as f:
            f.write(message + "\n")
    except Exception:
        pass


def main():
    log_debug("Wrapper started")
    buffer = []
    last_read_time = time.time()
    # Regular expression to extract hostname, program, and msg.
    pattern = re.compile(
        r"^hostname=(?P<hostname>\S+)\s+program=(?P<program>\S+)\s+msg=(?P<msg>.*)$"
    )

    while True:
        # Calculate how long to wait: time left until timeout expires
        timeout = AGGREGATION_TIMEOUT - (time.time() - last_read_time)
        if timeout < 0:
            timeout = 0

        # Wait for input on STDIN or timeout
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        if ready:
            # Read a single line from STDIN
            line = sys.stdin.readline()
            if line:
                buffer.append(line.strip())
                last_read_time = time.time()  # reset timeout on each new line
            else:
                # EOF received; break out of loop
                break
        else:
            # Timeout reached with no new input.
            if buffer:
                alerts = []
                for line in buffer:
                    match = pattern.match(line)
                    if match:
                        alerts.append(match.groupdict())
                    else:
                        # Fallback: if the line doesn't match, send the raw line.
                        alerts.append({"raw": line})
                log_debug("Aggregated alert: " + json.dumps(alerts))
                payload = {"alerts": alerts}
                try:
                    response = requests.post(POST_URL, json=payload, timeout=10)
                    log_debug("POST to {} returned status code: {}".format(POST_URL, response.status_code))
                except Exception as e:
                    log_debug("Error during POST: {}".format(e))
                # Clear buffer after sending
                buffer = []
            # Reset the last read time to avoid immediate repeated timeouts
            last_read_time = time.time()

if __name__ == "__main__":
    main()
        