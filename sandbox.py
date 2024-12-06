from network import wifi_list
import setting

for w in wifi_list.get_wifi_list(setting.SUDO_PSW):
    print(w)
