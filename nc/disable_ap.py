from network import utils
from network import wifi_manager
from network import netinfo
from setting import SUDO_PSW

def main():
    actual_mode = netinfo.get_wifi_mode(wifi_manager.AP_SSID, SUDO_PSW)
    if actual_mode == netinfo.WIFI_MODE_AP:
        utils.logger.info("Actually in AP mode, disabling AP mode")
        wifi_manager.enable_all_autoconnect(SUDO_PSW)
        wifi_manager.disconnect_from(wifi_manager.AP_CON_NAME, SUDO_PSW, check=False)
        wifi_manager.delete_connection(wifi_manager.AP_CON_NAME, SUDO_PSW, check=False)
        ssid = wifi_manager.reconnect_to_reacheable_known_network(SUDO_PSW)
        if ssid:
            utils.logger.info("Reconnected to %s", ssid)
        else:
            utils.logger.info("No known network available")
    else:
        utils.logger.info("Not in AP mode, nothing to do")
    return
    
if __name__ == "__main__":
    main()
    exit(0)