import time
import subprocess
from .utils import logger, format_result, run_sudo_command
from .netinfo import get_current_connection, get_network_info, get_wifi_list

WIFI_TYPE_NAME='wifi'
AP_CON_NAME='Hotspot'
AP_SSID='pibuddy'

def assert_ssid_valid(ssid:str)->bool:
    assert ssid, "SSID cannot be empty"
    assert ssid.isascii(), "SSID must be ASCII"
    assert len(ssid) <= 32, "SSID must be 32 characters or less"
    assert ' ' not in ssid, "SSID cannot contain spaces"

def assert_not_ap_ssid(ssid:str)->bool:
    assert ssid != AP_SSID, "SSID cannot be the same as the AP SSID"
    assert ssid != AP_CON_NAME, "SSID cannot be the same as the AP connection name"

def assert_password_valid(password:str)->bool:
    assert password, "Password cannot be empty"
    assert password.isascii(), "Password must be ASCII"
    assert len(password) >= 8, "Password must be at least 8 characters"
    assert len(password) <= 63, "Password must be 63 characters or less"
    assert ' ' not in password, "Password cannot contain spaces"

def create_network(ssid:str, password:str, sudo_password:str, autoconnect=True, check=True)->bool:
    logger.info(f"Attempting to create connection to {ssid}")
    assert_ssid_valid(ssid)
    assert_not_ap_ssid(ssid)
    assert_password_valid(password)

    kn = get_known_networks(sudo_password, check=True)
    if ssid in kn:
        logger.info(f"The network {ssid} already exists")
        if check:
            raise RuntimeError(f"The network {ssid} already exists")

    # Create the connection
    stdout, stderr = run_sudo_command([
        'nmcli', 'con', 'add',
        'type', 'wifi',
        'ifname', 'wlan0',
        'con-name', ssid,
        'ssid', ssid
    ], sudo_password)

    if stderr:
        logger.error(f"Connection creation failed: {stderr}")
        if check:
            raise RuntimeError(f"Connection creation failed: {stderr}")
        
    # Set the security settings
    stdout, stderr = run_sudo_command([
        'nmcli', 'con', 'modify', ssid,
        'wifi-sec.key-mgmt', 'wpa-psk',
        'wifi-sec.psk', password
    ], sudo_password)
    
    if stderr:
        logger.error(f"Setting security failed: {stderr}")
        if check:
            raise RuntimeError(f"Setting security failed: {stderr}")
    
    # Set autoconnect preference
    if not autoconnect:
        stdout, stderr = run_sudo_command([
            'nmcli', 'con', 'modify', ssid,
            'autoconnect', 'no'
        ], sudo_password)

    return True

def confirm_connection(ssid:str, sudo_password:str, attempts=10)->bool:
    for i in range(attempts):
        actual_ssid = get_current_connection(sudo_password)
        if actual_ssid == ssid:
            return True
        else:
            logger.info(f"Waiting for connection... {i+1}/{attempts}. Got {actual_ssid}")
            time.sleep(1)
    return False

def connect_to(ssid:str, password:str, sudo_password:str, autoconnect=False, check=True)->bool:
    logger.info(f"Attempting to connect to {ssid}")
    assert_ssid_valid(ssid)
    assert_password_valid(password)

    run_sudo_command(['nmcli', 'dev', 'wifi', 'list'], sudo_password)
    stdout, stderr = run_sudo_command(['nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password], sudo_password)
    if stderr:
        logger.error(f"Connection failed: {stderr}") 
        if check:
            raise RuntimeError(f"Connection failed: {stderr}")
    else:
        logger.info(f"Connection output: {stdout}")
    if not autoconnect:
        stdout, stderr = run_sudo_command(['nmcli', 'con', 'modify', ssid, 'autoconnect', 'no'], sudo_password)
    return confirm_connection(ssid, sudo_password)

        
def get_known_networks(sudo_password:str, check=True) -> list[str]:
    stdout, stderr = run_sudo_command(['nmcli', 'connection', 'show'], sudo_password)
    if stderr:
        logger.error(f"Connection failed: {stderr}") 
        if check:
            raise RuntimeError(f"Connection failed: {stderr}")
    else:
        networks = []
        for line in stdout.split('\n'):
            if WIFI_TYPE_NAME in line and AP_CON_NAME not in line:
                networks.append(line.split()[0])
        return networks

def disable_autoconnect(ssid:str, sudo_password:str):
    assert_ssid_valid(ssid)
    run_sudo_command(['nmcli', 'con', 'modify', ssid, 'autoconnect', 'no'], sudo_password)

def enable_autoconnect(ssid:str, sudo_password:str):
    assert_ssid_valid(ssid)
    run_sudo_command(['nmcli', 'con', 'modify', ssid, 'autoconnect', 'yes'], sudo_password)

def disable_all_autoconnect(sudo_password:str):
    known_networks = get_known_networks(sudo_password, check=False)
    for network in known_networks:
        if network == AP_CON_NAME:
            continue
        disable_autoconnect(network, sudo_password)

def enable_all_autoconnect(sudo_password:str):
    known_networks = get_known_networks(sudo_password, check=False)
    for network in known_networks:
        if network == AP_CON_NAME:
            continue
        enable_autoconnect(network, sudo_password)

def reconnect_to(ssid:str, sudo_password:str, check=True):
    assert_ssid_valid(ssid)
    run_sudo_command(['nmcli', 'dev', 'wifi', 'list'], sudo_password)
    stdout, stderr = run_sudo_command(['nmcli', 'con', 'up', ssid], sudo_password)
    if stderr:
        logger.error(f"Reconnection failed: {stderr}")
        if check:
            raise RuntimeError(f"Reconnection failed: {stderr}")
    else:
        logger.info(f"Reconnection output: {stdout}")
    return confirm_connection(ssid, sudo_password)

def reconnect_to_reacheable_known_network(sudo_passwork:str)->str:
    wl = get_wifi_list(sudo_passwork)
    for w in wl:
        if w.known and w.ssid != AP_SSID:
            ssid = w.ssid
            logger.info(f"Reconnecting to known network: {ssid}")
            if reconnect_to(ssid, sudo_passwork):
                return ssid

def disconnect_from(ssid:str, sudo_password:str, check=True):
    assert_ssid_valid(ssid)
    stdout, stderr = run_sudo_command(['nmcli', 'con', 'down', ssid], sudo_password)
    if stderr:
        logger.error(f"Disconnection failed: {stderr}")
        if check:
            raise RuntimeError(f"Disconnection failed: {stderr}")
    else:
        logger.info(f"Disconnection output: {stdout}")

def disconnect_current(sudo_password:str, check=True):
    current_ssid = get_current_connection(sudo_password)
    if current_ssid:
        disconnect_from(current_ssid, sudo_password, check=check)

def disconnect_ap(sudo_password:str, check=True):
    "Temporary disconnect from AP in order to scan wifi. Bcz some devices cannot be in AP and scan at the same time"
    disconnect_from(AP_CON_NAME, sudo_password, check=check)

def reconnect_ap(sudo_password:str, check=True):
    "Temporary reconnect to AP in order to scan wifi. Bcz some devices cannot be in AP and scan at the same time"
    reconnect_to(AP_CON_NAME, sudo_password, check=check)

def delete_connection(ssid:str, sudo_password:str, check=True):
    assert_ssid_valid(ssid)
    stdout, stderr = run_sudo_command(['nmcli', 'con', 'delete', ssid], sudo_password)
    if stderr:
        logger.error(f"Deletion failed: {stderr}")
        if check:
            raise RuntimeError(f"Deletion failed: {stderr}")
    else:
        logger.info(f"Deletion output: {stdout}")

def init_dhcp():
    dhcp_result = subprocess.run(['sudo', 'dhclient', 'wlan0'], 
                                capture_output=True,
                                text=True)
    if dhcp_result.returncode != 0:
        raise RuntimeError(f"DHCP configuration failed: {dhcp_result.stderr}")

    time.sleep(2)

def cleanup(original_ssid, sudo_password:str, check=True):
    try:              
        if original_ssid:
            logger.info(f"Reconnecting to original network: {original_ssid}")
            reconnect_to(original_ssid, sudo_password, check=check)
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def test_wifi_connection(ssid:str, password:str, sudo_password:str):
    """Test connection to WiFi network and return to original connection."""
    original_ssid = get_current_connection(sudo_password)
    logger.info(f"Current network: {original_ssid}")

    result_data = format_result()
    
    _connect_success = False
    try:
        _connect_success = connect_to(ssid, password, sudo_password)
        if _connect_success:
            logger.info("Successfully connected to network")
            logger.info("Requesting DHCP address")
            init_dhcp()
            logger.info("Getting network information after obtaining DHCP address.")
            network_info = get_network_info()
            result_data.update(network_info)
            result_data['result'] = 'OK'
            logger.info(f"Successfully obtained IP: {network_info['ip_address']}")
            logger.info(f"Disconnecting from {ssid} after testing")
            disconnect_from(ssid, sudo_password)
        else:
            logger.info(f"Delete {ssid} as it's failed.")
            delete_connection(ssid, sudo_password)
            raise RuntimeError(f"Failed to connect to {ssid}")
    except Exception as e:
        logger.error(f"Connection error: {e}")
        logger.info(f"Delete {ssid} as it's failed.")
        delete_connection(ssid, sudo_password)
        result_data['error'] = str(e)
    finally:
        if _connect_success:
            cleanup(original_ssid, sudo_password)

    return result_data

def start_ap_mode(ssid:str, password:str, sudo_password:str) -> bool:
    assert_ssid_valid(ssid)
    assert_password_valid(password)
    try:
        # Disable and delete the AP whatever it exists or not
        run_sudo_command(['nmcli', 'con', 'down', 'Hotspot'], sudo_password)
        run_sudo_command(['nmcli', 'con', 'delete', 'Hotspot'], sudo_password)
        # Stop any existing connection
        run_sudo_command(['nmcli', 'device', 'disconnect', 'wlan0'], sudo_password)
        
        # Create hotspot
        run_sudo_command([
            'nmcli', 'connection', 'add',
            'type', 'wifi',
            'ifname', 'wlan0',
            'con-name', 'Hotspot',
            'autoconnect', 'yes',
            'ssid', ssid,
            '802-11-wireless.mode', 'ap',
            '802-11-wireless-security.key-mgmt', 'none',
            '802-11-wireless-security.wep-key0', password
        ], sudo_password)
        
        # Configure IP address for AP
        run_sudo_command([
            'nmcli', 'connection', 'modify', 'Hotspot',
            'ipv4.method', 'shared'
        ], sudo_password)
        
        # Activate the hotspot
        run_sudo_command(['nmcli', 'connection', 'up', 'Hotspot'], sudo_password)
        logger.info("Successfully started AP mode")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start AP mode: {e}")
        return False