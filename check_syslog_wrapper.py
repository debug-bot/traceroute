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

from django.utils import timezone

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
    

    # 1) Fetch the alert rule data (keywords + mapping) once at startup
    alert_rule_data = get_alert_rule_data()
    print(alert_rule_data)
    # Prepare a regex pattern from the list of all unique keywords
    keywords = alert_rule_data["keywords"]
    if keywords:
        keyword_pattern = re.compile("|".join(keywords), re.IGNORECASE)
    else:
        # Fallback to a pattern that won't match anything
        keyword_pattern = re.compile("$^")

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
                        msg = data.get("msg", "")

                        # 2) Find all matching keywords in the msg
                        matched_keywords = keyword_pattern.findall(msg)
                        print(23,matched_keywords)
                        # 3) Collect rule names for each matched keyword
                        matched_rule_names = set()
                        for mk in matched_keywords:
                            # Compare ignoring case
                            for stored_kw, rule_names in alert_rule_data[
                                "keyword_map"
                            ].items():
                                if mk.lower() == stored_kw.lower():
                                    matched_rule_names.update(rule_names)

                        # If we found any matched rule names, update last_triggered
                        if matched_rule_names:
                            # Single DB query: update all matched rules in one go
                            AlertRule.objects.filter(
                                name__in=matched_rule_names
                            ).update(last_triggered=timezone.now())

                        # Add matched keywords and rule names to your payload
                        data["matching_keywords"] = matched_keywords
                        data["matched_rule_names"] = list(matched_rule_names)
                        alerts.append(data)
                    else:
                        # If the line doesn't match the expected format, include the raw line
                        alerts.append({"raw": line})

                log_debug("Aggregated alert: " + json.dumps(alerts))
                payload = {"alerts": alerts}
                try:
                    response = requests.post(POST_URL, json=payload, timeout=10)
                    log_debug(
                        f"POST to {POST_URL} returned status code: {response.status_code}"
                    )
                except Exception as e:
                    log_debug("Error during POST: {}".format(e))
                # Clear buffer after processing
                buffer = []
            # Reset the last read time for the next aggregation period
            last_read_time = time.time()


if __name__ == "__main__":
    main()
