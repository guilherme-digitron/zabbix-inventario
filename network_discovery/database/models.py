"""
Modelos de Banco de Dados
"""

from datetime import datetime
from enum import Enum


class DeviceType(str, Enum):
    """Tipos de dispositivos de rede"""
    ROUTER = 'router'
    SWITCH = 'switch'
    ACCESS_POINT = 'access_point'
    SERVER = 'server'
    DESKTOP = 'desktop'
    NOTEBOOK = 'notebook'
    SMARTPHONE = 'smartphone'
    PRINTER = 'printer'
    IOT = 'iot'
    UNKNOWN = 'unknown'


class DeviceStatus(str, Enum):
    """Status de um dispositivo"""
    ONLINE = 'online'
    OFFLINE = 'offline'
    UNKNOWN = 'unknown'


class ConnectionType(str, Enum):
    """Tipo de conexão entre dispositivos"""
    CONFIRMED = 'confirmed'      # Comprovada por LLDP, CDP, SNMP, MAC table
    INFERRED = 'inferred'         # Inferida por correlação de dados
    UNKNOWN = 'unknown'           # Desconhecida


class DiscoveryMethod(str, Enum):
    """Métodos de descoberta utilizados"""
    NMAP = 'nmap'
    ARP = 'arp'
    SNMP = 'snmp'
    LLDP = 'lldp'
    CDP = 'cdp'
    ZABBIX = 'zabbix'
    MANUAL = 'manual'


class Device:
    """Representa um dispositivo na rede"""
    
    def __init__(self, ip, mac=None, hostname=None):
        self.ip = ip
        self.mac = mac
        self.hostname = hostname
        self.device_type = DeviceType.UNKNOWN
        self.status = DeviceStatus.UNKNOWN
        self.os = 'Desconhecido'
        self.model = 'Desconhecido'
        self.vendor = 'Desconhecido'
        self.open_ports = []
        self.services = []
        self.interfaces = []
        self.last_seen = datetime.now()
        self.first_seen = datetime.now()
        self.discovery_methods = set()  # Métodos que descobriram este dispositivo
        self.metadata = {}  # Dados adicionais

    def add_discovery_method(self, method):
        """Adiciona um método de descoberta"""
        if isinstance(method, str):
            self.discovery_methods.add(method)
        else:
            self.discovery_methods.add(method.value)

    def to_dict(self):
        """Converte o dispositivo para dicionário"""
        return {
            'ip': self.ip,
            'mac': self.mac or 'Desconhecido',
            'hostname': self.hostname or 'Desconhecido',
            'type': self.device_type.value,
            'status': self.status.value,
            'os': self.os,
            'model': self.model,
            'vendor': self.vendor,
            'open_ports': self.open_ports,
            'services': self.services,
            'interfaces': self.interfaces,
            'last_seen': self.last_seen.isoformat(),
            'first_seen': self.first_seen.isoformat(),
            'discovery_methods': list(self.discovery_methods),
            'metadata': self.metadata
        }


class NetworkInterface:
    """Representa uma interface de rede"""
    
    def __init__(self, device_ip, interface_name, ip=None, mac=None, status='up'):
        self.device_ip = device_ip
        self.interface_name = interface_name
        self.ip = ip
        self.mac = mac
        self.status = status
        self.vlan = None
        self.mtu = None
        self.speed = None

    def to_dict(self):
        return {
            'device_ip': self.device_ip,
            'interface_name': self.interface_name,
            'ip': self.ip or 'Desconhecido',
            'mac': self.mac or 'Desconhecido',
            'status': self.status,
            'vlan': self.vlan,
            'mtu': self.mtu,
            'speed': self.speed
        }


class Connection:
    """Representa uma conexão entre dois dispositivos"""
    
    def __init__(self, source_ip, destination_ip):
        self.source_ip = source_ip
        self.destination_ip = destination_ip
        self.source_interface = None
        self.destination_interface = None
        self.connection_type = ConnectionType.UNKNOWN
        self.discovery_method = None
        self.confidence = 0  # 0-100
        self.confirmed = False
        self.last_seen = datetime.now()
        self.metadata = {}

    def to_dict(self):
        return {
            'source_ip': self.source_ip,
            'destination_ip': self.destination_ip,
            'source_interface': self.source_interface,
            'destination_interface': self.destination_interface,
            'type': self.connection_type.value,
            'method': self.discovery_method,
            'confidence': self.confidence,
            'confirmed': self.confirmed,
            'last_seen': self.last_seen.isoformat(),
        }


class Port:
    """Representa uma porta aberta em um dispositivo"""
    
    def __init__(self, device_ip, port_number, protocol='tcp', state='open'):
        self.device_ip = device_ip
        self.port_number = port_number
        self.protocol = protocol
        self.state = state
        self.service = 'Desconhecido'
        self.version = 'Desconhecido'
        self.last_seen = datetime.now()

    def to_dict(self):
        return {
            'device_ip': self.device_ip,
            'port': self.port_number,
            'protocol': self.protocol,
            'state': self.state,
            'service': self.service,
            'version': self.version,
            'last_seen': self.last_seen.isoformat(),
        }


class Scan:
    """Representa um scan de descoberta de rede"""
    
    def __init__(self, network_cidr, manual=False):
        self.scan_id = None  # Será gerado pelo banco de dados
        self.network_cidr = network_cidr
        self.start_time = datetime.now()
        self.end_time = None
        self.status = 'running'  # running, completed, failed
        self.devices_found = 0
        self.devices_online = 0
        self.devices_new = 0
        self.devices_offline = 0
        self.manual = manual
        self.notes = ''
        self.methods_used = []

    def to_dict(self):
        duration = None
        if self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        
        return {
            'scan_id': self.scan_id,
            'network_cidr': self.network_cidr,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'duration_seconds': duration,
            'devices_found': self.devices_found,
            'devices_online': self.devices_online,
            'devices_new': self.devices_new,
            'devices_offline': self.devices_offline,
            'manual': self.manual,
            'methods_used': self.methods_used,
            'notes': self.notes
        }


class DeviceHistory:
    """Histórico de alterações de um dispositivo"""
    
    def __init__(self, device_ip, change_type, old_value=None, new_value=None):
        self.device_ip = device_ip
        self.timestamp = datetime.now()
        self.change_type = change_type  # ip_change, mac_change, hostname_change, online, offline, new, removed
        self.old_value = old_value
        self.new_value = new_value
        self.scan_id = None

    def to_dict(self):
        return {
            'device_ip': self.device_ip,
            'timestamp': self.timestamp.isoformat(),
            'change_type': self.change_type,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'scan_id': self.scan_id
        }
