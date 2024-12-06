# Presentation
This project is to make a pi-like (Resberry Pi, Orange Pi) mini PC like a mini server for travelers. The idea is when it's startup, it detects automatically the best way to make possible connections from client. Then, if possible and necessary, it starts a web server to make configurations, start, stop services etc..

# Start up operations
## Connection option
1. When starts up, try to connect to the saved Wifi network. If succeed, go to "Start web service" section
2. If unable to connect to a saved Wifi, or no such saved Wifi is set, then go to "Start Hot spot Wifi" section

It's not possible to read & write directly in the sd card so the option "put a start up config file" is not possible.

## Start Hot spot Wifi
1. Starts a Wifi Hot Spot with a preset name and password.
2. Start the web service.

## Start the web servce
What ever the Wifi connection is via a Hot Spot or via joining to a Wifi network, the pibuddy web service is always necessary.

# Service install and start up
## Systemd method
Configure the systemd so that make it possible to start the service as a deamon service.

# Problems
## Start AP
Tried many options, still unable to create a secured AP. Only WEP without password AP actually work.\
Tried wap-psk, AP can be found by other devices, but unable to connect to it. Checked wpa-suppliant logs, NetworkManager logs, no idea.\
Found some warning logs like 
- Failed to set beacon parameters
- nl80211 driver interface is not designed to be used with ap_scan=2;
- wlan0: CTRL-EVENT-SCAN-FAILED ret=-5
Tried oae method, failed with wpa-suppliant timeout error message during AP creation phase.
Tried wifi.scan-rand-mac-address=no in /etc/NetworkManager/NetworkManager.conf : does not work neither, nothing changed.