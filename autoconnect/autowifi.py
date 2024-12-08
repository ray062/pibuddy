import time
import subprocess
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WifiManager:
    WIFI_KEYWORD = 'wifi' # some OS/nmcli versions use '802-11-wireless'
    HOTSPOT_CONNAME= 'Hotspot'
    def __init__(self, ap_ssid: str, ap_password: str):
        self.ap_ssid = ap_ssid
        self.ap_password = ap_password
        self.actual_wifi = None
        self.ap_activated = False
        
    def get_known_networks(self) -> list:
        try:
            result = subprocess.run(['nmcli', 'connection', 'show'],
                                  capture_output=True, text=True)
            networks = []
            for line in result.stdout.split('\n'):
                if self.WIFI_KEYWORD in line:
                    networks.append(line.split()[0])
            return networks
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get known networks: {e}")
            return []

    def get_actual_wifi(self, check=False) -> Optional[str]:
        try:
            cmd = "nmcli -t -f active,ssid dev wifi | grep '^yes'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
            for line in result.stdout.split('\n'):
                return line.split(':')[1]
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get actual WiFi: {e}")
            return None

    def is_connected_to_wifi(self) -> bool:
        try:
            result = subprocess.run(['nmcli', '-t', '-f', 'DEVICE,STATE',
                                   'device', 'status'],
                                  capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'wlan0:connected' in line:
                    self.actual_wifi = self.get_actual_wifi(check=True)
                    self.ap_activated = self.actual_wifi == self.ap_ssid
                    logger.info(f"Connected to WiFi: {self.actual_wifi}")
                    return True
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to check connection status: {e}")
            return False


    def get_network_list(self, attemps=3, waitting_time=5):
        for _ in range(attemps):
            result = subprocess.run(['nmcli', '-t', '-f', 'SSID', 'device', 'wifi', 'list'],
                                    capture_output=True, text=True)
            available_networks = result.stdout.split('\n')
            if len(available_networks) > 0:
                logger.info(f"Available networks: {available_networks}")
                return available_networks
            else:
                logger.warning("No available networks found. Retrying...")
                time.sleep(waitting_time)
        logger.error("Failed to get available networks after multiple attempts.")
        return []

    def try_connect_known_networks(self) -> bool:
        known_networks = self.get_known_networks()
        logger.info(f"Known networks: {known_networks}")
        
        # First, ensure WiFi is enabled
        try:
            subprocess.run(['nmcli', 'radio', 'wifi', 'on'], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to enable WiFi: {e}")
            return False

        # Scan for available networks
        try:
            subprocess.run(['nmcli', 'con', 'down', self.HOTSPOT_CONNAME], check=False)
            subprocess.run(['nmcli', 'device', 'wifi', 'rescan'], check=False)
        except subprocess.CalledProcessError:
            logger.warning("Failed to rescan WiFi networks")

        # Get available networks 
        try:
            available_networks = self.get_network_list()
            for network in known_networks:
                if network == self.HOTSPOT_CONNAME:
                    continue
                elif network in available_networks:
                    try:
                        subprocess.run(['nmcli', 'connection', 'up', network], check=True)
                        logger.info(f"Successfully connected to {network}")
                        return True
                    except subprocess.CalledProcessError:
                        logger.warning(f"Failed to connect to {network}")
                        continue
                subprocess.run(['nmcli', 'con', 'modify', network, 'autoconnect', 'yes'], check=False)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list WiFi networks: {e}")
        
        return False

    def start_ap_mode(self) -> bool:
        try:
            # Disable and delete the AP whatever it exists or not
            subprocess.run(['nmcli', 'con', 'down', self.HOTSPOT_CONNAME], check=False)
            subprocess.run(['nmcli', 'con', 'delete', self.HOTSPOT_CONNAME], check=False)
            # Stop any existing connection
            subprocess.run(['nmcli', 'device', 'disconnect', 'wlan0'], check=False)
            
            # Create hotspot
            subprocess.run([
                'nmcli', 'connection', 'add',
                'type', 'wifi',
                'ifname', 'wlan0',
                'con-name', self.HOTSPOT_CONNAME,
                'autoconnect', 'yes',
                'ssid', self.ap_ssid,
                '802-11-wireless.mode', 'ap',
                '802-11-wireless-security.key-mgmt', 'none',
                '802-11-wireless-security.wep-key0', self.ap_password
            ], check=True)
            
            # Configure IP address for AP
            subprocess.run([
                'nmcli', 'connection', 'modify', self.HOTSPOT_CONNAME,
                'ipv4.method', 'shared'
            ], check=True)
            
            # Activate the hotspot
            subprocess.run(['nmcli', 'connection', 'up', self.HOTSPOT_CONNAME], check=True)
            logger.info("Successfully started AP mode")
            self.ap_activated = True
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start AP mode: {e}")
            return False

    def manage_connection(self):
        # Disconnect from the Hotspot at the beginning, whatever the status it is.
        subprocess.run(['nmcli', 'con', 'down', self.HOTSPOT_CONNAME], check=False)
        subprocess.run(['nmcli', 'con', 'delete', self.HOTSPOT_CONNAME], check=False)
        subprocess.run(['nmcli', 'dev', 'wifi', 'rescan'], check=False)
        time.sleep(5)
        subprocess.run(['nmcli', 'dev', 'wifi', 'list'], check=False)
        while True:
            if not self.is_connected_to_wifi():
                logger.info("Not connected to WiFi, trying to connect...")
                if not self.try_connect_known_networks():
                    logger.info("No known networks available, starting AP mode...")
                    self.start_ap_mode()
            else:
                logger.info("Connected to WiFi, no action needed, quite the service.") 
                return
            time.sleep(30)  # Check every 30 seconds


def main():
    # Configure your desired AP settings
    AP_SSID = "pibuddy"
    AP_PASSWORD = "Pibuddy123"  # At least 8 characters
    logger.info("Start the service, creating wifi_manager")
    wifi_manager = WifiManager(AP_SSID, AP_PASSWORD)
    wifi_manager.manage_connection()

if __name__ == "__main__":
    main()
    exit(0)
