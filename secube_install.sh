#!/bin/bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install git -y
sudo apt-get install python3-pip -y
sudo pip3 install pyserial --break-system-packages
sudo pip3 install pyserial pyyaml tqdm  --break-system-packages

#alternives UART Mapping
echo "enable_uart=1" | sudo tee -a /boot/firmware/config.txt
#legt UART Port für GPIO 12 und 13 fest
echo "dtoverlay=uart5" | sudo tee -a /boot/firmware/config.txt

#Repo muss öffentlich sein
git clone https://github.com/MrGorillaz/SeCubeSmart.git
cd SeCubeSmart


