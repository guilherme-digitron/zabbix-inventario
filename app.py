from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Minimal sample data. Replace this with real data source as needed.
SAMPLE_DEVICES = [
    {"hostname": "host1.example.local", "ip": "192.168.1.10", "mac": "AA:BB:CC:DD:EE:01", "model": "Dell R740", "os": "Ubuntu 20.04"},
    {"hostname": "host2.example.local", "ip": "192.168.1.11", "mac": "AA:BB:CC:DD:EE:02", "model": "HP ProLiant DL360", "os": "CentOS 7"},
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/devices')
def api_devices():
    # In the future, replace SAMPLE_DEVICES with real backend/database/API.
    return jsonify(SAMPLE_DEVICES)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
