#!/bin/bash
# Script para parar e desabilitar o serviço

echo "Removendo serviço network-discovery..."

sudo systemctl stop network-discovery
sudo systemctl disable network-discovery
sudo rm /etc/systemd/system/network-discovery.service
sudo systemctl daemon-reload

echo "Serviço removido."
