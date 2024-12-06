#!/bin/bash
sudo systemctl stop wpa_supplicant
sudo systemctl stop NetworkManager

nmcli connection delete pibuddy

nmcli con add \
	type wifi \
	ifname wlan0 \
	con-name "pibuddy" \
	autoconnect no \
	ssid "pibuddy" \
	mode ap \
	ipv4.method shared \
	ipv4.addresses "192.168.2.1/24" \
	wifi.band bg \
	wifi.channel 6 \
	ipv6.method shared \
	wifi-sec.key-mgmt wpa-psk \
	wifi-sec.psk "123456789"  \
	wifi-sec.proto rsn \
	wifi-sec.pairwise ccmp \
	wifi-sec.group ccmp \
	802-11-wireless.mode ap \
	802-11-wireless.powersave 0 \
	connection.auth-retries 2 \
	802-11-wireless.security.auth-alg open

sudo systemctl restart NetworkManager

sleep 2
# Enable the connection
nmcli con up pibuddy

echo "=== Connection Status ==="
nmcli device status

echo "=== Authentication Settings ==="
nmcli connection show pibuddy | grep -i "auth\|security"


# To stop:
# nmcli con down pibuddy

# to delete :
# nmcli con delete pibuddy

