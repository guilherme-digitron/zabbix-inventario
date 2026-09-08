"""
Scanner ARP para Descoberta Local de Rede
"""

import logging
import subprocess
import re
from typing import List
from network_discovery.database.models import Device, DeviceType, DeviceStatus, DiscoveryMethod
from network_discovery import config
from .base_scanner import BaseScanner


class ARPScanner(BaseScanner):
    """Scanner baseado em ARP para descoberta local"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.arp_pattern = re.compile(
            r'(?P<ip>\d+\.\d+\.\d+\.\d+)\s+'
            r'(?:.*?)\s+'
            r'(?P<mac>(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2})'
        )
        self.vendor_db = self._load_vendor_db()

    def is_available(self) -> bool:
        """Verifica se o ARP está disponível"""
        try:
            result = subprocess.run(['arp', '-h'], capture_output=True, timeout=2)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def scan(self, network_cidr: str) -> List[Device]:
        """Executa scan ARP de descoberta local"""
        self.clear()
        self.logger.info(f'Iniciando scan ARP em {network_cidr}')
        
        try:
            self._scan_arp_table()
            self.logger.info(f'Scan ARP concluído. {len(self.devices)} dispositivos encontrados')
        except Exception as e:
            self.logger.error(f'Erro durante scan ARP: {e}')
        
        return self.get_discovered_devices()

    def _scan_arp_table(self):
        """Lê a tabela ARP do sistema"""
        try:
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                self.logger.warning(f'Erro ao executar arp: {result.stderr}')
                return
            
            for line in result.stdout.split('\n'):
                self._parse_arp_line(line)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f'Erro ao ler tabela ARP: {e}')

    def _parse_arp_line(self, line: str):
        """Faz parse de uma linha da tabela ARP"""
        line = line.strip()
        if not line:
            return
        
        # Diferentes formatos de ARP em diferentes sistemas
        # Linux: hostname (ip) at mac [ether]
        # Windows: ip mac type
        # macOS: hostname (ip) at mac
        
        match = self.arp_pattern.search(line)
        if not match:
            return
        
        ip = match.group('ip')
        mac = match.group('mac').upper()
        
        device = Device(ip, mac)
        device.add_discovery_method(DiscoveryMethod.ARP)
        device.status = DeviceStatus.ONLINE
        device.vendor = self._get_vendor_from_mac(mac)
        
        # Extrair hostname se disponível
        parts = line.split()
        if parts and not parts[0].startswith(ip):
            hostname = parts[0].split('(')[0]
            if hostname:
                device.hostname = hostname
        
        self._add_or_update_device(device)

    def _load_vendor_db(self) -> dict:
        """Carrega banco de dados de fabricantes (OUI)"""
        # TODO: Integrar com banco de dados OUI completo
        # Por enquanto, usar um mini banco de dados
        return {
            '00:00:5E': 'IANA',
            '00:07:EB': 'Juniper',
            '00:0D:3B': 'Cisco',
            '00:15:17': 'Mikrotik',
            '08:00:27': 'Virtualbox',
            '52:54:00': 'KVM',
            'B8:27:EB': 'Raspberry Pi',
            'DC:A6:32': 'Raspberry Pi',
            'E0:94:67': 'Realtek',
            '00:1A:2B': 'Cisco',
            '00:11:85': 'D-Link',
            '00:1C:10': 'Cisco',
        }

    def _get_vendor_from_mac(self, mac: str) -> str:
        """Obtém o fabricante a partir do MAC (OUI)"""
        oui = mac[:8].upper()
        return self.vendor_db.get(oui, 'Desconhecido')
