import os
import socket
import tempfile
import json
import subprocess
from dataclasses import dataclass

from flask import Flask, render_template, request, jsonify

from network import netinfo
from network import wifi_manager
import setting

app = Flask(__name__)


def get_ip_address():
    # Get the primary IP address of the machine
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = "127.0.0.1"
    finally:
        s.close()
    return ip_address

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/')
def hello_world():
    # Get the IP address of the machine
    ip_address = get_ip_address()
    # Get the list of available Wi-Fi networks
    wl = list(netinfo.get_wifi_list(setting.SUDO_PSW))
    kwn = netinfo.get_known_networks(setting.SUDO_PSW)
    unreacheable_known = [k for k in kwn if k not in [w.ssid for w in wl]]
    reacheable_known = [w for w in wl if w.known]
    # actual_state values 
    # WIFI_MODE_UNKNOWN=-1
    # WIFI_MODE_UNCONNECT=0
    # WIFI_MODE_INFRA=1
    # WIFI_MODE_AP=2
    actual_state = netinfo.get_wifi_mode(wifi_manager.AP_SSID, setting.SUDO_PSW)
    
    # Return the HTML response
    return render_template('wifi_networks.html', networks=wl, ip_address=ip_address, 
                           unreacheable_known = unreacheable_known, 
                           actual_state = actual_state, reacheable_known_count=len(reacheable_known))

@app.route('/switch_ap', methods=['POST', 'GET'])
def switch_ap():
    # Execute the test_wifi.py script
    result = subprocess.run(
        ['python3', '-m', 'nc.start_ap'],
        cwd=setting.APP_PATH,
        capture_output=True,
        text=True
    )

    # Parse the output
    if result.stdout:
        return jsonify(json.loads(result.stdout))
    else:
        return jsonify({
            'result': 'ERROR',
            'error': result.stderr or 'No output from test script'
        }), 500
    
@app.route('/disable_ap', methods=['POST', 'GET'])
def disable_ap():
    # Execute the test_wifi.py script
    result = subprocess.run(
        ['python3', '-m', 'nc.disable_ap'],
        cwd=setting.APP_PATH,
        capture_output=True,
        text=True
    )

    # Parse the output
    if result.stdout:
        return jsonify(json.loads(result.stdout))
    else:
        return jsonify({
            'result': 'ERROR',
            'error': result.stderr or 'No output from test script'
        }), 500

@app.route('/test_network', methods=['POST'])
def test_network():
    try:
        # Get credentials from the request
        data = request.get_json()
        
        # Validate required fields
        if not data or 'ssid' not in data or 'password' not in data:
            return jsonify({
                'result': 'ERROR',
                'error': 'SSID and password are required in JSON body'
            }), 400

        ssid = data['ssid'].strip()
        password = data['password'].strip()

        # Create a temporary file to store credentials
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            credentials = {
                'ssid': ssid,
                'password': password,
                'sudo_password': setting.SUDO_PSW
            }
            json.dump(credentials, temp_file)
            temp_file_path = temp_file.name

        try:
            # Execute the test_wifi.py script
            result = subprocess.run(
                ['python3', '-m', 'nc.test_wifi', temp_file_path],
                cwd=setting.APP_PATH,
                capture_output=True,
                text=True
            )

            # Parse the output
            if result.stdout:
                return jsonify(json.loads(result.stdout))
            else:
                return jsonify({
                    'result': 'ERROR',
                    'error': result.stderr or 'No output from test script'
                }), 500

        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        return jsonify({
            'result': 'ERROR',
            'error': str(e)
        }), 500

@app.get('/shutdown')
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

if __name__ == '__main__':
    # Run the app on all network interfaces
    app.run(host='0.0.0.0', port=5000)
