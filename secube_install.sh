#!/bin/bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install git -y
#Repo muss öffentlich sein
git clone https://github.com/MrGorillaz/SeCubeSmart.git
cd SeCubeSmart
#alternives UART Mapping
echo "dtoverlay=uart4,txd4_pin=12,rxd4_pin=13" | sudo tee -a /boot/firmware/config.txt
