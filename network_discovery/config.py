"""
Configurações do Sistema de Descoberta de Rede
"""

import os
from pathlib import Path

# Caminhos
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
DB_PATH = DATA_DIR / 'network_discovery.db'

# Criar diretórios se não existirem
DATA_DIR.mkdir(exist_ok=True)

# Configurações de Rede
DEFAULT_NETWORK_CIDR = os.getenv('NETWORK_CIDR', '192.168.1.0/24')
DEFAULT_SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', '600'))  # 10 minutos em segundos

# Configurações de Scanner
NMAP_ENABLED = os.getenv('NMAP_ENABLED', 'true').lower() == 'true'
ARP_ENABLED = os.getenv('ARP_ENABLED', 'true').lower() == 'true'
SNMP_ENABLED = os.getenv('SNMP_ENABLED', 'false').lower() == 'true'
LLDP_ENABLED = os.getenv('LLDP_ENABLED', 'false').lower() == 'true'
CDP_ENABLED = os.getenv('CDP_ENABLED', 'false').lower() == 'true'

# Configurações SNMP
SNMP_COMMUNITY = os.getenv('SNMP_COMMUNITY', 'public')
SNMP_VERSION = os.getenv('SNMP_VERSION', '2c')
SNMP_PORT = int(os.getenv('SNMP_PORT', '161'))
SNMP_TIMEOUT = int(os.getenv('SNMP_TIMEOUT', '2'))
SNMP_RETRIES = int(os.getenv('SNMP_RETRIES', '1'))

# Configurações Nmap
NMAP_TIMEOUT = int(os.getenv('NMAP_TIMEOUT', '300'))  # 5 minutos
NMAP_AGGRESSIVE = os.getenv('NMAP_AGGRESSIVE', 'false').lower() == 'true'
NMAP_INTENSITY = int(os.getenv('NMAP_INTENSITY', '7'))  # 0-9, 7 é default
NMAP_TIMING = os.getenv('NMAP_TIMING', 'T3')  # T0-T5

# Configurações ARP
ARP_TIMEOUT = int(os.getenv('ARP_TIMEOUT', '10'))
ARP_RETRIES = int(os.getenv('ARP_RETRIES', '2'))

# Configurações de Discovery
DISCOVERY_TIMEOUT = int(os.getenv('DISCOVERY_TIMEOUT', '30'))
CONNECT_TIMEOUT = int(os.getenv('CONNECT_TIMEOUT', '5'))
READ_TIMEOUT = int(os.getenv('READ_TIMEOUT', '10'))

# Limites de velocidade (para não sobrecarregar a rede)
MAX_PARALLEL_SCANS = int(os.getenv('MAX_PARALLEL_SCANS', '10'))
SCAN_RATE_LIMIT = int(os.getenv('SCAN_RATE_LIMIT', '100'))  # hosts por segundo

# Banco de Dados
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))
DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '10'))

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'network_discovery.log')

# Segurança
RESPECT_RATE_LIMITS = True
NO_AGGRESSIVE_SCANNING = True
NO_EXPLOITATION = True
VALIDATE_CIDRS = True

# Retorno de dados
UNKNOWN_VALUE = 'Desconhecido'
