import os
import socket
import tempfile
import json
import time
import subprocess

from flask import Flask, render_template, request, jsonify

from network import netinfo
from network import wifi_manager
from syscmd import state
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

    actual_state = netinfo.get_wifi_mode(wifi_manager.AP_SSID, setting.SUDO_PSW)
    kwn = netinfo.get_known_networks(setting.SUDO_PSW)


    # Get the list of available Wi-Fi networks
    wl = list((w for w in netinfo.get_wifi_list(setting.SUDO_PSW) if w.ssid))

    unreacheable_known = [k for k in kwn if k.ssid not in [w.ssid for w in wl]]

    # Return the HTML response
    return render_template('wifi_networks.html', networks=wl, ip_address=ip_address, 
                           unreacheable_known = unreacheable_known, 
                           actual_state = actual_state)

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

@app.route('/create_network', methods=['POST'])
def create_network():
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

        wifi_manager.create_network(ssid, password, setting.SUDO_PSW)
        return jsonify({
            'result': 'OK',
            'ssid': ssid
        })
    except Exception as e:
        return jsonify({
            'result': 'ERROR',
            'error': str(e)
        }), 500
    

@app.route('/toggle_autoconnect', methods=['POST'])
def toggle_autoconnect():
    try:
        # Get credentials from the request
        data = request.get_json()

        # Validate required fields
        if not data or 'ssid' not in data or 'enabled' not in data:
            return jsonify({
                'result': 'ERROR',
                'error': 'SSID and enabled are required in JSON body'
            }), 400
        
        ssid = data['ssid'].strip()
        enabled = data['enabled']
        assert type(enabled) == bool, 'Invalid enabled value'

        if enabled:
            wifi_manager.enable_autoconnect(ssid, setting.SUDO_PSW)
        else:
            wifi_manager.disable_autoconnect(ssid, setting.SUDO_PSW)

        return jsonify({
            'result': 'OK',
            'ssid': ssid
        })
    except Exception as e:
        return jsonify({
            'result': 'ERROR',
            'error': str(e)
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

@app.route('/poweroff', methods=['POST'])
def poweroff():
    try:
        data = request.get_json()
        if not data or 'delay' not in data:
            return jsonify({
                'result': 'ERROR',
                'error': 'delay is required in JSON body'
            }), 400
        
        delay = int(data.get('delay', 0))
        time.sleep(delay)
        state.poweroff(setting.SUDO_PSW)
        return jsonify({'result': 'OK'})
    except Exception as e:
        return jsonify({
            'result': 'ERROR',
            'error': str(e)
        }), 500

@app.route('/delete_network', methods=['POST'])
def delete_network():
    data = request.get_json()
    ssid = data.get('ssid')
    if not ssid:
        return jsonify({'error': 'SSID is required'}), 400
    
    try:
        wifi_manager.delete_connection(ssid, setting.SUDO_PSW)
        return jsonify({'message': 'Network deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/connect_network', methods=['POST'])
def connect_network():
    try:
        data = request.get_json()
        if not data or 'ssid' not in data:
            return jsonify({
                'result': 'ERROR',
                'error': 'SSID is required in JSON body'
            }), 400
        
        ssid = data['ssid'].strip()
        delay = int(data.get('delay', 0))
        time.sleep(delay)
        
        # Get current connection before attempting to change
        current_connection = wifi_manager.get_current_connection(setting.SUDO_PSW)
        
        try:
            # Attempt to reconnect to the specified network
            if wifi_manager.reconnect_to(ssid, setting.SUDO_PSW):
                return jsonify({
                    'result': 'OK',
                    'ssid': ssid
                })
            else:
                raise RuntimeError("Failed to connect to network")
        except Exception as e:
            # If connection fails, attempt to fall back to original network
            if current_connection:
                wifi_manager.cleanup(current_connection, setting.SUDO_PSW)
            return jsonify({
                'result': 'ERROR',
                'error': str(e)
            }), 500
            
    except Exception as e:
        return jsonify({
            'result': 'ERROR',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Run the app on all network interfaces
    app.run(host='0.0.0.0', port=5000)
