"""
Scanner Nmap para Descoberta de Rede
"""

import logging
import subprocess
import xml.etree.ElementTree as ET
from typing import List, Optional
import shutil
from network_discovery.database.models import Device, DeviceType, DeviceStatus, DiscoveryMethod, Port
from network_discovery import config
from .base_scanner import BaseScanner


class NmapScanner(BaseScanner):
    """Scanner baseado em Nmap"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.nmap_path = self._find_nmap()
        self.os_signatures = {
            'Linux': ['linux'],
            'Windows': ['windows', 'winnt'],
            'macOS': ['darwin', 'osx'],
            'Android': ['android'],
            'iOS': ['ios', 'iphone'],
            'Router': ['router', 'cisco', 'mikrotik', 'ddwrt'],
            'Printer': ['printer', 'hp', 'xerox', 'canon'],
        }
        self.service_ports = {
            22: ('SSH', 'secure shell'),
            80: ('HTTP', 'web'),
            443: ('HTTPS', 'secure web'),
            445: ('SMB', 'file sharing'),
            3306: ('MySQL', 'database'),
            5432: ('PostgreSQL', 'database'),
            3389: ('RDP', 'remote desktop'),
            8080: ('HTTP Alt', 'web'),
            8443: ('HTTPS Alt', 'secure web'),
            161: ('SNMP', 'network management'),
        }

    def _find_nmap(self) -> Optional[str]:
        """Localiza o caminho do nmap no sistema"""
        nmap_path = shutil.which('nmap')
        if not nmap_path:
            self.logger.warning('Nmap não encontrado no sistema')
            return None
        self.logger.info(f'Nmap encontrado em: {nmap_path}')
        return nmap_path

    def is_available(self) -> bool:
        """Verifica se o nmap está disponível"""
        return self.nmap_path is not None

    def scan(self, network_cidr: str) -> List[Device]:
        """Executa scan completo de descoberta de rede"""
        if not self.is_available():
            self.logger.error('Nmap não está disponível')
            return []
        
        self.clear()
        self.logger.info(f'Iniciando scan Nmap em {network_cidr}')
        
        try:
            # Descoberta de hosts
            self._discover_hosts(network_cidr)
            
            # Scan de portas e serviços
            self._scan_ports(network_cidr)
            
            # Detecção de SO
            self._detect_os(network_cidr)
            
            self.logger.info(f'Scan Nmap concluído. {len(self.devices)} dispositivos encontrados')
        except Exception as e:
            self.logger.error(f'Erro durante scan Nmap: {e}')
        
        return self.get_discovered_devices()

    def _discover_hosts(self, network_cidr: str):
        """Descobre hosts ativos na rede (ping sweep)"""
        self.logger.info(f'Descobrindo hosts em {network_cidr}...')
        
        cmd = [
            self.nmap_path,
            '-sn',  # Ping scan
            network_cidr,
            '-oX', '-'  # Output XML to stdout
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=config.NMAP_TIMEOUT)
            if result.returncode not in [0, 1]:  # 1 é normal quando nenhum host responde
                self.logger.error(f'Nmap discovery retornou erro: {result.stderr}')
                return
            
            self._parse_nmap_xml(result.stdout, 'discovery')
        except subprocess.TimeoutExpired:
            self.logger.error('Nmap discovery timeout')
        except Exception as e:
            self.logger.error(f'Erro na descoberta de hosts: {e}')

    def _scan_ports(self, network_cidr: str):
        """Escaneia portas comuns e identifica serviços"""
        self.logger.info(f'Escaneando portas em {network_cidr}...')
        
        # Portas mais comuns
        ports = '22,80,443,445,3306,5432,3389,8080,8443,161,25,53,67,68,69,123,135,139,389,636,1433,1521,5000,5432,5984,6379,7000-7100,8000-8100,9000,9200,27017,50070'
        
        cmd = [
            self.nmap_path,
            '-p', ports,
            '-sV',  # Service version detection
            '--version-intensity', '9',
            network_cidr,
            '-oX', '-'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=config.NMAP_TIMEOUT)
            if result.returncode not in [0, 1]:
                self.logger.warning(f'Nmap port scan retornou: {result.stderr}')
                return
            
            self._parse_nmap_xml(result.stdout, 'ports')
        except subprocess.TimeoutExpired:
            self.logger.error('Nmap port scan timeout')
        except Exception as e:
            self.logger.error(f'Erro no scan de portas: {e}')

    def _detect_os(self, network_cidr: str):
        """Tenta detectar o SO dos hosts"""
        self.logger.info(f'Detectando SO em {network_cidr}...')
        
        cmd = [
            self.nmap_path,
            '-O',  # OS detection
            '--osscan-guess',
            network_cidr,
            '-oX', '-'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=config.NMAP_TIMEOUT)
            if result.returncode not in [0, 1]:
                self.logger.warning(f'Nmap OS detection retornou: {result.stderr}')
                return
            
            self._parse_nmap_xml(result.stdout, 'os')
        except subprocess.TimeoutExpired:
            self.logger.error('Nmap OS detection timeout')
        except Exception as e:
            self.logger.error(f'Erro na detecção de SO: {e}')

    def _parse_nmap_xml(self, xml_output: str, scan_type: str):
        """Faz parse do XML do Nmap"""
        try:
            root = ET.fromstring(xml_output)
        except ET.ParseError as e:
            self.logger.error(f'Erro ao fazer parse XML do Nmap: {e}')
            return
        
        for host in root.findall('.//host'):
            status = host.find('./status')
            if status is None or status.get('state') != 'up':
                continue
            
            # Extrair IP e MAC
            ip = None
            mac = None
            
            for address in host.findall('./address'):
                addr_type = address.get('addrtype')
                if addr_type == 'ipv4':
                    ip = address.get('addr')
                elif addr_type == 'mac':
                    mac = address.get('addr')
            
            if not ip:
                continue
            
            # Obter ou criar dispositivo
            if ip not in self.devices:
                device = Device(ip, mac)
                device.add_discovery_method(DiscoveryMethod.NMAP)
                self.devices[ip] = device
            else:
                device = self.devices[ip]
                if mac and not device.mac:
                    device.mac = mac
            
            # Processar portas
            for port_elem in host.findall('.//port'):
                port_state = port_elem.find('./state')
                if port_state is None:
                    continue
                
                port_num = int(port_elem.get('portid'))
                protocol = port_elem.get('protocol', 'tcp')
                state = port_state.get('state')
                
                if state == 'open':
                    port = Port(ip, port_num, protocol, state)
                    
                    # Tentar identificar serviço
                    service_elem = port_elem.find('./service')
                    if service_elem is not None:
                        port.service = service_elem.get('name', 'Desconhecido')
                        port.version = service_elem.get('version', 'Desconhecido')
                    elif port_num in self.service_ports:
                        port.service = self.service_ports[port_num][0]
                    
                    device.open_ports.append(port.to_dict())
            
            # Processar SO
            for osmatch in host.findall('.//osmatch'):
                os_name = osmatch.get('name')
                if os_name:
                    device.os = os_name
                    device.device_type = self._classify_device_type(os_name)
                    break
            
            device.status = DeviceStatus.ONLINE

    def _classify_device_type(self, os_name: str) -> DeviceType:
        """Classifica o tipo de dispositivo baseado no nome do SO"""
        os_lower = os_name.lower()
        
        for device_type_name, keywords in self.os_signatures.items():
            for keyword in keywords:
                if keyword in os_lower:
                    if device_type_name == 'Router':
                        return DeviceType.ROUTER
                    elif device_type_name == 'Printer':
                        return DeviceType.PRINTER
                    elif device_type_name == 'Windows':
                        return DeviceType.DESKTOP  # Pode ser refinado depois
                    elif device_type_name == 'Linux':
                        return DeviceType.UNKNOWN  # Precisa de mais contexto
                    elif device_type_name == 'Android':
                        return DeviceType.SMARTPHONE
                    elif device_type_name == 'iOS':
                        return DeviceType.SMARTPHONE
        
        return DeviceType.UNKNOWN
