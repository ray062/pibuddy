# determine the actual status:
# 1- already in AP mode : nothing to do
# 2- Connected as client in a network :
#    1- disconnect from that network
#    2- set auto-connect to no to all known-networks
#    3- start AP mode
# 3- Not connected to any network : start AP mode


from network import utils
from network import wifi_manager
from network import netinfo
from setting import SUDO_PSW

def main():
    actual_mode = netinfo.get_wifi_mode(wifi_manager.AP_SSID, SUDO_PSW)
    if actual_mode == netinfo.WIFI_MODE_AP:
        utils.logger.info("Already in AP mode, nothing to do")
        return
    elif actual_mode == netinfo.WIFI_MODE_INFRA:
        utils.logger.info("Connected as client in a network, disconnecting...")
        # Disconnect from the current network
        wifi_manager.disable_all_autoconnect(SUDO_PSW)
        wifi_manager.disconnect_current(SUDO_PSW, check=False)
    utils.logger.info("Starting AP mode...")
    wifi_manager.start_ap_mode(wifi_manager.AP_SSID, "Pibuddy123", SUDO_PSW)
    
if __name__ == "__main__":
    main()
    exit(0)