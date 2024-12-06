sudo nmcli con down Hotspot
sudo nmcli con delete Hotspot
sudo nmcli con add type wifi ifname wlan0 con-name Hotspot autoconnect yes ssid pibuddy mode ap
sudo nmcli con modify Hotspot 802-11-wireless.mode ap ipv4.method shared

# wpa-psk : connection failed directly
# sudo nmcli con modify Hotspot 802-11-wireless-security.key-mgmt wpa-psk 802-11-wireless-security.psk "Pibuddy123"

# connection OK but no password, insecure
sudo nmcli con modify Hotspot 802-11-wireless-security.key-mgmt none 802-11-wireless-security.wep-key0 "Pibuddy123"

# wpa-psk band bg : same, connection failed, no log shown in NetworkManager service
# sudo nmcli con modify Hotspot 802-11-wireless.mode ap 802-11-wireless.band bg 802-11-wireless-security.key-mgmt wpa-psk ipv4.method shared 802-11-wireless-security.psk "Pibuddy123"

# sae : supplicant_timeout issue
# sudo nmcli con modify Hotspot 802-11-wireless-security.key-mgmt sae 802-11-wireless-security.psk "Pibuddy123"

sudo nmcli con down Colink
sudo nmcli con modify Colink autoconnect no
sudo nmcli con up Hotspot
