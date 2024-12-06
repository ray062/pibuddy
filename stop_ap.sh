sudo nmcli con modify Colink autoconnect yes
sudo nmcli con down Hotspot
sudo nmcli con delete Hotspot
sudo nmcli con up Colink
sudo nmcli dev wifi list


