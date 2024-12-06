import re
from dataclasses import dataclass
import subprocess
from .utils import logger, run_sudo_command

@dataclass
class WIFINetwrok:
    in_use: bool
    bssid: str
    ssid: str
    mode: str
    chan: int
    rate: str
    signal: int
    bars: str
    security: str
    known: bool = False

    def __init__(self, line:str):
        line = line.replace('\\:', '-')
        line_parts = line.split(":")
        
        if line_parts[0] == '*':
            self.in_use = True
        else:
            self.in_use = False

        self.bssid, self.ssid, self.mode, self.chan = line_parts[1:5]
        self.bssid = self.bssid.replace('-', ':')
        self.chan = int(self.chan)
        self.rate, self.signal, self.bars = line_parts[5:8]
        self.signal = int(self.signal)
        self.security = ' '.join(line_parts[8:])

WIFI_MODE_UNKNOWN=-1
WIFI_MODE_UNCONNECT=0
WIFI_MODE_INFRA=1
WIFI_MODE_AP=2


def get_current_connection(sudo_password:str)->str: 
    """Get current WiFi connection details."""
    try:
        stdout, stderr = run_sudo_command( ['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'], sudo_password)
        for l in stdout.strip().split('\n'):
            if l.startswith('yes'):
                return l.split(':')[1].strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get current connection: {e}")
        raise RuntimeError(f"Failed to get current connection: {str(e)}")
    except IndexError:
        return None

def get_wifi_mode(ap_ssid, sudo_password:str)->int:
    current_ssid = get_current_connection(sudo_password)
    if current_ssid == ap_ssid:
        return WIFI_MODE_AP 
    
    stdout, stderr = run_sudo_command(['nmcli', '-t', '-f', 'MODE', 'dev', 'wifi'], sudo_password)
    if stderr and 'password for' not in stderr:
        logger.error(f"Connection failed: {stderr}")
    else:
        status = stdout.split('\n')
        if 'AP' in status:
            return WIFI_MODE_AP
        elif 'Infra' in status:
            return WIFI_MODE_INFRA
        else:
            return WIFI_MODE_UNCONNECT

def get_ip_address():
    """Get IP address for wlan0."""  
    result = subprocess.run(['ip', 'addr', 'show', 'dev', 'wlan0'],
                          capture_output=True,
                          text=True)

    ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
    return ip_match.group(1) if ip_match else None

def get_gateway():
    """Get gateway IP for wlan0."""
    result = subprocess.run(['ip', 'route', 'show', 'dev', 'wlan0', 'default'],
                          capture_output=True,
                          text=True)
    if result.returncode == 0:
        match = re.search(r'default via (\d+\.\d+\.\d+\.\d+)', result.stdout)
        if match:
            return match.group(1)
    return None

def get_dns_servers():
    """Get DNS servers from resolv.conf."""
    dns_servers = []
    try:
        with open('/etc/resolv.conf', 'r') as f:
            for line in f:
                if line.startswith('nameserver'):
                    dns_servers.append(line.split()[1])
    except Exception as e:
        logger.warning(f"Failed to read DNS information: {e}")
    return dns_servers

def get_dhcp_server():
    """Get DHCP server IP from lease files."""
    # Try dhcpcd lease file
    try:
        with open('/var/lib/dhcpcd/dhcpcd-wlan0.lease', 'r') as f:
            match = re.search(r'dhcp_server_identifier=(\d+\.\d+\.\d+\.\d+)', 
                            f.read())
            if match:
                return match.group(1)
    except FileNotFoundError:
        pass

    # Try dhclient lease file
    try:
        with open('/var/lib/dhcp/dhclient.leases', 'r') as f:
            match = re.search(r'option dhcp-server-identifier (\d+\.\d+\.\d+\.\d+)',
                            f.read())
            if match:
                return match.group(1)
    except FileNotFoundError:
        pass

    return None

def get_network_info():
    """Get all network information."""
    try:
        ip_address = get_ip_address()
        if not ip_address:
            raise RuntimeError("No IP address assigned")

        gateway = get_gateway()
        dhcp_server = get_dhcp_server() or gateway
        dns_servers = get_dns_servers()

        return {
            'ip_address': ip_address,
            'dhcp_server': dhcp_server,
            'gateway': gateway,
            'dns_servers': dns_servers
        }
    except Exception as e:
        logger.error(f"Error getting network information: {e}")
        raise

def get_known_networks(sudo_password:str) -> list:
    stdout, stderr = run_sudo_command(['nmcli', 'connection', 'show'], sudo_password)
    if stderr:
        logger.error(f"Failed to get known networks: {stderr}")
        return []
    else:
        networks = []
        for line in stdout.split('\n'):
            if 'wifi' in line:
                networks.append(line.split()[0])
        return networks

def get_wifi_list(sudo_password:str):
    known_networks = get_known_networks(sudo_password) 
    stdout, stderr = run_sudo_command(['nmcli', '-t', 'dev', 'wifi', 'list'], sudo_password)
    if stderr:
        logger.error(f"Error: {stderr}")
        return None
    # Skip the first line of stdout because it's header
    for line in stdout.splitlines()[1:]:
        try:
            wn = WIFINetwrok(line)
            wn.known = wn.ssid in known_networks
            yield wn
        except Exception as e:
            logger.error(f"Error: {e}")
            logger.error(f"Line: {line}")
            continue