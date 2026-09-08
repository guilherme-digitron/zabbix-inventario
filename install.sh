#!/bin/bash
# Script de instalação para Debian/Ubuntu/Raspberry Pi

echo "========================================"
echo "Instalador - Sistema de Descoberta de Rede"
echo "========================================"
echo ""

# Verificar se é root
if [[ $EUID -ne 0 ]]; then
   echo "Este script deve ser executado como root (use sudo)"
   exit 1
fi

echo "[1/5] Atualizando pacotes do sistema..."
apt-get update
apt-get upgrade -y

echo "[2/5] Instalando dependências de sistema..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nmap \
    git \
    net-tools \
    curl

echo "[3/5] Criando ambiente virtual Python..."
python3 -m venv venv
source venv/bin/activate

echo "[4/5] Instalando dependências Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[5/5] Configurando permissões..."
chmod +x app.py
mkdir -p network_discovery/data

echo ""
echo "========================================"
echo "Instalação concluída!"
echo "========================================"
echo ""
echo "Para iniciar o serviço:"
echo "  1. Ativar ambiente virtual:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Executar aplicação:"
echo "     python3 app.py"
echo ""
echo "  3. Acessar no navegador:"
echo "     http://$(hostname -I | awk '{print $1}'):5000/rede"
echo ""
echo "Configuração de variáveis de ambiente:"
echo "  export NETWORK_CIDR='192.168.1.0/24'"
echo "  export SCAN_INTERVAL='600'"
echo "  export NMAP_ENABLED='true'"
echo "  export ARP_ENABLED='true'"
echo ""
