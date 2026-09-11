"""
Classe Base para Scanners
"""

import logging
from abc import ABC, abstractmethod
from typing import List
from network_discovery.models import Device


class BaseScanner(ABC):
    """Classe base abstrata para todos os scanners"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.devices = {}  # ip -> Device

    @abstractmethod
    def scan(self, network_cidr: str) -> List[Device]:
        """Executa o scan de descoberta na rede"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica se o scanner está disponível no sistema"""
        pass

    def get_discovered_devices(self) -> List[Device]:
        return list(self.devices.values())

    def _add_or_update_device(self, device: Device) -> Device:
        key = device.ip
        if key in self.devices:
            existing = self.devices[key]
            if device.mac and not existing.mac:
                existing.mac = device.mac
            if device.hostname and not existing.hostname:
                existing.hostname = device.hostname
            if device.os != 'Desconhecido' and existing.os == 'Desconhecido':
                existing.os = device.os
            for method in device.discovery_methods:
                existing.add_discovery_method(method)
            return existing
        else:
            self.devices[key] = device
            return device

    def clear(self):
        self.devices.clear()
