"""
Network Discovery Module
Sistema de descoberta, inventário e mapeamento automático de rede TCP/IP
"""

from datetime import datetime

__version__ = '1.0.0'
__author__ = 'Guilherme Digitron'
__description__ = 'Network Discovery and Topology Mapping System'

# Inicializar logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
