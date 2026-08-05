import os
import requests
import json
import ast
import re
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Configuration: set these as environment variables for production
ZABBIX_URL = os.getenv('ZABBIX_URL')  # e.g. http://192.168.3.141/api_jsonrpc.php
ZABBIX_API_TOKEN = os.getenv('ZABBIX_API_TOKEN')  # your Zabbix API token (auth)

# Keys used in your environment (as provided)
MAC_KEY = 'wmi.getall[root\\cimv2,"select MACAddress from win32_networkadapter where PhysicalAdapter=True"]'
MODEL_KEY = 'wmi.get[root\\cimv2,SELECT Model FROM Win32_ComputerSystem]'

MAC_REGEX = re.compile(r'([0-9A-Fa-f]{2}(?:[:\-][0-9A-Fa-f]{2}){5})')


def zabbix_request(method, params):
    if not ZABBIX_URL:
        raise RuntimeError('ZABBIX_URL is not configured. Set the ZABBIX_URL environment variable.')
    if not ZABBIX_API_TOKEN:
        raise RuntimeError('ZABBIX_API_TOKEN is not configured. Set the ZABBIX_API_TOKEN environment variable.')

    payload = {
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'id': 1,
        'auth': ZABBIX_API_TOKEN,
    }
    headers = {'Content-Type': 'application/json-rpc'}
    r = requests.post(ZABBIX_URL, json=payload, headers=headers, timeout=15)
    r.raise_for_status()
    data = r.json()
    if 'error' in data:
        raise RuntimeError(f"Zabbix API error: {data['error']}")
    return data.get('result')


def extract_macs_from_value(value):
    """Extract MAC addresses from a Zabbix item lastvalue.

    The value can be:
    - a JSON string representing a list of objects: [{"MACAddress": "..."}, ...]
    - a plain string that may contain MAC addresses
    - an empty or unusual format

    Returns a comma-separated string with normalized MACs (XX:XX:...)
    or empty string if none found.
    """
    if not value:
        return ''

    candidates = []

    # Try to interpret as JSON
    if isinstance(value, (list, dict)):
        data = value
    else:
        # value is a string: try json.loads, then ast.literal_eval as fallback
        data = None
        try:
            data = json.loads(value)
        except Exception:
            try:
                # sometimes Zabbix stores a Python-like repr; ast.literal_eval can handle it
                data = ast.literal_eval(value)
            except Exception:
                data = None

    # If data is a list/dict, try to find MACAddress fields
    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict):
                for v in entry.values():
                    if not v:
                        continue
                    # v might be a MAC or string containing a MAC
                    found = MAC_REGEX.findall(str(v))
                    for m in found:
                        candidates.append(m)
    elif isinstance(data, dict):
        for v in data.values():
            if not v:
                continue
            found = MAC_REGEX.findall(str(v))
            for m in found:
                candidates.append(m)
    else:
        # Treat the original value as text and extract MAC patterns
        found = MAC_REGEX.findall(str(value))
        for m in found:
            candidates.append(m)

    # Normalize (replace - with : and uppercase) and deduplicate while preserving order
    normalized = []
    seen = set()
    for m in candidates:
        nm = m.replace('-', ':').upper()
        if nm not in seen:
            seen.add(nm)
            normalized.append(nm)

    return ', '.join(normalized)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/devices')
def api_devices():
    """Fetch hosts from Zabbix and return simplified device list.

    Required environment variables:
      - ZABBIX_URL (e.g. http://192.168.3.141/api_jsonrpc.php)
      - ZABBIX_API_TOKEN (the API auth token)

    The MAC and model are retrieved from items with the keys you provided.
    Status is derived from interface availability (available == '1' -> online).
    """
    try:
        # 1) Get hosts with interfaces and inventory
        params = {
            'output': ['hostid', 'host'],
            'selectInterfaces': ['interfaceid', 'ip', 'main', 'useip', 'available'],
            'selectInventory': 'extend',
        }
        hosts = zabbix_request('host.get', params)

        if not hosts:
            return jsonify([])

        hostids = [h['hostid'] for h in hosts]

        # 2) Get items for MAC and Model across all hosts in one call
        item_params = {
            'output': ['itemid', 'hostid', 'lastvalue', 'key_'],
            'hostids': hostids,
            'filter': {'key_': [MAC_KEY, MODEL_KEY]},
            'preservekeys': True,
        }
        items = zabbix_request('item.get', item_params)

        # Map items by hostid
        items_by_host = {}
        for it in items or []:
            hid = it.get('hostid')
            if hid not in items_by_host:
                items_by_host[hid] = []
            items_by_host[hid].append(it)

        devices = []
        for h in hosts:
            hostname = h.get('host') or ''

            # IP from interfaces (useip == '1' or main == '1')
            ip = ''
            for iface in h.get('interfaces', []) or []:
                try:
                    if str(iface.get('useip', '0')) == '1' or str(iface.get('main', '0')) == '1':
                        ip = iface.get('ip') or ip
                        if ip:
                            break
                except Exception:
                    continue

            # Determine online/offline from interface availability if available
            status = 'unknown'
            for iface in h.get('interfaces', []) or []:
                av = iface.get('available')
                if av is None:
                    continue
                try:
                    avs = str(av)
                except Exception:
                    avs = ''
                if avs == '1':
                    status = 'online'
                    break
                if avs == '2' and status != 'online':
                    status = 'offline'

            inv = h.get('inventory') or {}

            # Start with inventory-based fields as fallback
            mac = inv.get('macaddress_a') or inv.get('macaddress') or inv.get('mac') or inv.get('macaddress_b') or ''
            model = inv.get('model') or inv.get('hardware') or inv.get('type') or ''
            os_field = inv.get('os') or inv.get('os_full') or inv.get('osfull') or ''

            # Override with item values if present
            for it in items_by_host.get(h['hostid'], []):
                key = it.get('key_') or ''
                last = it.get('lastvalue') or ''
                if key == MAC_KEY and last:
                    extracted = extract_macs_from_value(last)
                    if extracted:
                        mac = extracted
                if key == MODEL_KEY and last:
                    # last may be a plain string or JSON - we'll try to parse
                    model = str(last)

            devices.append({
                'hostname': hostname,
                'ip': ip,
                'mac': mac,
                'model': model,
                'os': os_field,
                'status': status,
            })

        return jsonify(devices)

    except RuntimeError as e:
        return jsonify({'error': str(e)}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Network error when contacting Zabbix: {e}'}), 502
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {e}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
