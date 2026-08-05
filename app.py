import os
import requests
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Configuration: set these as environment variables for production
ZABBIX_URL = os.getenv('ZABBIX_URL')  # e.g. http://192.168.3.141/api_jsonrpc.php
ZABBIX_API_TOKEN = os.getenv('ZABBIX_API_TOKEN')  # your Zabbix API token (auth)

# Fallback behavior: do not hardcode sensitive tokens in the repo.
# If env vars are not set, the API will return an error instructing how to configure them.

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
    r = requests.post(ZABBIX_URL, json=payload, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    if 'error' in data:
        raise RuntimeError(f"Zabbix API error: {data['error']}")
    return data.get('result')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/devices')
def api_devices():
    """Fetch hosts from Zabbix and return simplified device list.

    Required environment variables:
      - ZABBIX_URL (e.g. http://192.168.3.141/api_jsonrpc.php)
      - ZABBIX_API_TOKEN (the API auth token)
    """
    try:
        # Request hosts with interfaces and full inventory
        params = {
            'output': ['host'],
            'selectInterfaces': ['ip', 'main', 'useip'],
            'selectInventory': 'extend',
        }
        hosts = zabbix_request('host.get', params)

        devices = []
        for h in hosts:
            hostname = h.get('host') or ''

            # Get primary IP from interfaces (useip == '1' or main == '1')
            ip = ''
            for iface in h.get('interfaces', []) or []:
                # interface fields can be strings
                if str(iface.get('useip', '0')) == '1' or str(iface.get('main', '0')) == '1':
                    ip = iface.get('ip') or ip
                    if ip:
                        break
            # If not found on interfaces, leave empty

            inv = h.get('inventory') or {}

            # MAC: try multiple common inventory keys
            mac = inv.get('macaddress_a') or inv.get('macaddress') or inv.get('mac') or inv.get('macaddress_b') or ''
            # model and os
            model = inv.get('model') or inv.get('hardware') or inv.get('type') or ''
            os_field = inv.get('os') or inv.get('os_full') or inv.get('osfull') or ''

            devices.append({
                'hostname': hostname,
                'ip': ip,
                'mac': mac,
                'model': model,
                'os': os_field,
            })

        return jsonify(devices)

    except RuntimeError as e:
        return jsonify({'error': str(e)}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Network error when contacting Zabbix: {e}'}), 502
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {e}'}), 500


if __name__ == '__main__':
    # For local testing you can set the env vars before running.
    # Example (Linux/macOS):
    # export ZABBIX_URL='http://192.168.3.141/api_jsonrpc.php'
    # export ZABBIX_API_TOKEN='your_token_here'
    app.run(host='0.0.0.0', port=5000, debug=True)
