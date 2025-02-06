# core/zabbix_utils.py

import requests
import json

ZABBIX_API_URL = 'http://23.141.136.114/api_jsonrpc.php'
ZABBIX_AUTH_TOKEN = '345aaed36cc684ce7b3ffe52fd97a8d831d27fccf492b43f14880f749aada0b4'

def zabbix_request(method, params, auth=ZABBIX_AUTH_TOKEN, request_id=1):
    """
    Generic function to make a JSON-RPC request to the Zabbix API.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "auth": auth,
        "id": request_id,
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(ZABBIX_API_URL, json=payload, headers=headers)
    response.raise_for_status()  # Raise an error for bad HTTP status codes
    result = response.json()
    if 'error' in result:
        raise Exception(f"Zabbix API Error: {result['error']}")
    return result.get('result')

def get_router_interfaces(hostids=None):
    """
    Example: Poll Zabbix for router interface data.
    
    Adjust the parameters according to the Zabbix API documentation.
    For example, you might want to retrieve interface details for a given host.
    """
    params = {
        "output": ["interfaceid", "hostid", "ip", "port", "error"],
        "selectItems": ["itemid", "name", "key_", "lastvalue", "counters"],
        # Optionally, filter by host IDs if you have them
        # "hostids": hostids,
    }
    return zabbix_request("hostinterface.get", params)
