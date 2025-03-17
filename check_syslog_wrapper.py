#!/home/txfiber/traceroute/venv/bin/python
import os
import sys
import django
import select
import time
import requests
import json
import re

# Ensure the current directory (where manage.py is) is in the Python path.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from app.models import Alert, AlertRule  # Import your Alert model

DEBUG_LOG = "/var/log/rsyslog_wrapper/check_syslog_wrapper_debug.log"
POST_URL = "https://fastcli.com/check-syslog/"  # Django endpoint to receive POST data
AGGREGATION_TIMEOUT = 2  # seconds


def log_debug(message):
    try:
        with open(DEBUG_LOG, "a") as f:
            f.write(message + "\n")
    except Exception:
        pass


def get_keywords():
    """
    Retrieve the comma-separated keywords string from the database.
    Modify the query as needed based on your model structure.
    """
    try:
        alert = Alert.objects.first()  # adjust the query logic as required
        if alert and hasattr(alert, "keywords_str"):
            return alert.keywords_str
    except Exception as e:
        log_debug("Error fetching keywords from DB: {}".format(e))
    # Fallback if DB query fails
    return "BGP, OSPF, RPD, ISIS, MPLS"


def get_alert_rule_data():
    """
    Retrieve and combine the comma-separated keywords from all AlertRule objects,
    and keep track of which rule(s) each keyword belongs to.

    Returns a dictionary:
    {
      "keywords": [list_of_all_unique_keywords],
      "keyword_map": {
          "KEYWORD_1": ["Alert Rule Name A", "Alert Rule Name B"],
          "KEYWORD_2": ["Alert Rule Name C"],
          ...
      }
    }
    """
    data = {"keywords": [], "keyword_map": {}}

    try:
        alert_rules = AlertRule.objects.all()
        all_keywords = set()

        for rule in alert_rules:
            # rule.syslog_strings might be "SNMP_TRAP_LINK_DOWN, SNMP_TRAP_LINK_UP"
            if rule.syslog_strings:
                # Split by commas and strip whitespace
                splitted_keywords = [
                    kw.strip() for kw in rule.syslog_strings.split(",") if kw.strip()
                ]
                for kw in splitted_keywords:
                    all_keywords.add(kw)
                    if kw not in data["keyword_map"]:
                        data["keyword_map"][kw] = []
                    # Append this rule's name for that keyword
                    data["keyword_map"][kw].append(rule.name)

        data["keywords"] = list(all_keywords)

    except Exception as e:
        log_debug(f"Error fetching keywords from DB: {e}")

        # Fallback if DB query fails or there's no data
        fallback_keywords = ["BGP", "OSPF", "RPD", "ISIS", "MPLS"]
        data["keywords"] = fallback_keywords
        # Associate all fallback keywords with a generic rule name
        data["keyword_map"] = {kw: ["Fallback Alert Rule"] for kw in fallback_keywords}

    return data


def main():
    log_debug("Wrapper started")
    buffer = []
    last_read_time = time.time()
    # Regex to extract hostname, program, and msg from the input
    header_pattern = re.compile(
        r"^hostname=(?P<hostname>\S+)\s+program=(?P<program>\S+)\s+msg=(?P<msg>.*)$"
    )

    while True:
        # Calculate remaining time until aggregation timeout
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
                last_read_time = time.time()  # reset timer with each new line
            else:
                # EOF reached; exit loop
                break
        else:
            # Timeout reached without new input: process the buffered lines
            if buffer:
                alerts = []
                for line in buffer:
                    match = header_pattern.match(line)
                    if match:
                        data = match.groupdict()
                        # Retrieve keywords from the DB
                        keywords_str = get_keywords()
                        # Create a list of keywords from the comma-separated string
                        keywords = [kw.strip() for kw in keywords_str.split(",")]
                        # Compile a regex pattern to match any of the keywords (case-insensitive)
                        keyword_pattern = re.compile("|".join(keywords), re.IGNORECASE)
                        msg = data.get("msg", "")
                        matching_keywords = keyword_pattern.findall(msg)
                        # Add matching keywords to the data dictionary
                        data["matching_keywords"] = matching_keywords
                        alerts.append(data)
                    else:
                        # If the line doesn't match the expected format, include the raw line
                        alerts.append({"raw": line})
                log_debug("Aggregated alert: " + json.dumps(alerts))
                payload = {"alerts": alerts}
                try:
                    response = requests.post(POST_URL, json=payload, timeout=10)
                    log_debug(
                        "POST to {} returned status code: {}".format(
                            POST_URL, response.status_code
                        )
                    )
                except Exception as e:
                    log_debug("Error during POST: {}".format(e))
                # Clear buffer after processing
                buffer = []
            # Reset the last read time for the next aggregation period
            last_read_time = time.time()


if __name__ == "__main__":
    main()
