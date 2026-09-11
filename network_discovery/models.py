"""
Modelo mínimo de dispositivo de rede.

Sem banco de dados: os objetos vivem apenas durante a execução de um
mapeamento e são descartados/serializados em seguida.
"""

from enum import Enum


class DeviceType(str, Enum):
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


class Device:
    """Representa um dispositivo descoberto durante um mapeamento"""

    def __init__(self, ip, mac=None, hostname=None):
        self.ip = ip
        self.mac = mac
        self.hostname = hostname
        self.device_type = DeviceType.UNKNOWN
        self.os = 'Desconhecido'
        self.vendor = 'Desconhecido'
        self.open_ports = []          # lista de dicts {port, protocol, service}
        self.discovery_methods = set()

    def add_discovery_method(self, method):
        self.discovery_methods.add(method if isinstance(method, str) else method.value)

    def to_dict(self):
        return {
            'ip': self.ip,
            'mac': self.mac or 'Desconhecido',
            'hostname': self.hostname or 'Desconhecido',
            'type': self.device_type.value if isinstance(self.device_type, DeviceType) else self.device_type,
            'os': self.os,
            'vendor': self.vendor,
            'open_ports': self.open_ports,
            'discovery_methods': sorted(self.discovery_methods),
        }
