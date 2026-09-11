"""
Scanner Nmap para Descoberta de Rede
"""

import logging
import subprocess
import shutil
import xml.etree.ElementTree as ET
from typing import List, Optional
from network_discovery.models import Device, DeviceType
from network_discovery import config
from .base_scanner import BaseScanner


class NmapScanner(BaseScanner):
    """Scanner baseado em Nmap"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.nmap_path = self._find_nmap()
        self.os_signatures = {
            'router': ['router', 'cisco', 'mikrotik', 'ddwrt'],
            'printer': ['printer', 'hp', 'xerox', 'canon'],
            'desktop': ['windows', 'winnt'],
            'smartphone': ['android', 'ios', 'iphone'],
        }
        self.service_names = {
            22: 'SSH', 80: 'HTTP', 443: 'HTTPS', 445: 'SMB',
            3306: 'MySQL', 5432: 'PostgreSQL', 3389: 'RDP',
            8080: 'HTTP Alt', 8443: 'HTTPS Alt', 161: 'SNMP',
        }

    def _find_nmap(self) -> Optional[str]:
        path = shutil.which('nmap')
        if not path:
            self.logger.warning('Nmap não encontrado no sistema')
        return path

    def is_available(self) -> bool:
        return self.nmap_path is not None

    def scan(self, network_cidr: str) -> List[Device]:
        """Executa descoberta + portas + tentativa de SO em uma única chamada"""
        if not self.is_available():
            self.logger.error('Nmap não está disponível')
            return []

        self.clear()
        self.logger.info(f'Iniciando scan Nmap em {network_cidr}')

        cmd = [
            self.nmap_path,
            '-sV', '--version-intensity', '5',
            '-O', '--osscan-guess',
            '-p', config.COMMON_PORTS,
            network_cidr,
            '-oX', '-',
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=config.NMAP_TIMEOUT)
            if result.returncode not in (0, 1):
                self.logger.warning(f'Nmap retornou: {result.stderr.strip()}')
            self._parse_nmap_xml(result.stdout)
            self.logger.info(f'Scan Nmap concluído. {len(self.devices)} dispositivos encontrados')
        except subprocess.TimeoutExpired:
            self.logger.error('Nmap timeout')
        except Exception as e:
            self.logger.error(f'Erro durante scan Nmap: {e}')

        return self.get_discovered_devices()

    def _parse_nmap_xml(self, xml_output: str):
        try:
            root = ET.fromstring(xml_output)
        except ET.ParseError as e:
            self.logger.error(f'Erro ao fazer parse XML do Nmap: {e}')
            return

        for host in root.findall('.//host'):
            status = host.find('./status')
            if status is None or status.get('state') != 'up':
                continue

            ip, mac = None, None
            for address in host.findall('./address'):
                addr_type = address.get('addrtype')
                if addr_type == 'ipv4':
                    ip = address.get('addr')
                elif addr_type == 'mac':
                    mac = address.get('addr')

            if not ip:
                continue

            device = self.devices.get(ip) or Device(ip, mac)
            device.add_discovery_method('nmap')
            if mac and not device.mac:
                device.mac = mac

            hostnames = host.find('./hostnames')
            if hostnames is not None:
                hn = hostnames.find('./hostname')
                if hn is not None and hn.get('name') and not device.hostname:
                    device.hostname = hn.get('name')

            for port_elem in host.findall('.//port'):
                port_state = port_elem.find('./state')
                if port_state is None or port_state.get('state') != 'open':
                    continue

                port_num = int(port_elem.get('portid'))
                protocol = port_elem.get('protocol', 'tcp')
                service_name = self.service_names.get(port_num, 'Desconhecido')

                service_elem = port_elem.find('./service')
                if service_elem is not None and service_elem.get('name'):
                    service_name = service_elem.get('name')

                device.open_ports.append({
                    'port': port_num,
                    'protocol': protocol,
                    'service': service_name,
                })

            classified = False
            for osmatch in host.findall('.//osmatch'):
                os_name = osmatch.get('name')
                if os_name:
                    device.os = os_name
                    device.device_type = self._classify_device_type(ip, os_name, device)
                    classified = True
                    break

            if not classified:
                device.device_type = self._classify_device_type(ip, '', device)

            self.devices[ip] = device

    def _classify_device_type(self, ip: str, os_name: str, device: Device) -> DeviceType:
        if ip.endswith('.1'):
            return DeviceType.ROUTER

        os_lower = os_name.lower()
        for type_name, keywords in self.os_signatures.items():
            if any(k in os_lower for k in keywords):
                return DeviceType(type_name)

        ports = {p['port'] for p in device.open_ports}
        if 161 in ports:
            return DeviceType.SWITCH
        if 631 in ports or 9100 in ports:
            return DeviceType.PRINTER
        if ports & {80, 443, 8080, 8443} and 22 in ports:
            return DeviceType.SERVER

        return device.device_type if device.device_type != DeviceType.UNKNOWN else DeviceType.UNKNOWN
