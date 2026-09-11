"""
Configurações do Módulo de Mapeamento de Rede (sem persistência)
"""

import os

# Rede padrão sugerida quando o usuário não informa outra
DEFAULT_NETWORK_CIDR = os.getenv('NETWORK_CIDR', '192.168.1.0/24')

# Scanners
NMAP_ENABLED = os.getenv('NMAP_ENABLED', 'true').lower() == 'true'
ARP_ENABLED = os.getenv('ARP_ENABLED', 'true').lower() == 'true'

# Timeouts (segundos)
NMAP_TIMEOUT = int(os.getenv('NMAP_TIMEOUT', '120'))
ARP_TIMEOUT = int(os.getenv('ARP_TIMEOUT', '10'))

# Portas comuns verificadas no scan de serviços
COMMON_PORTS = '22,23,53,80,135,139,161,443,445,3306,3389,5432,8080,8443'

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'network_discovery.log')

# Segurança / limites
NO_AGGRESSIVE_SCANNING = True
NO_EXPLOITATION = True
