"""
Classe Base para Scanners
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from network_discovery.database.models import Device


class BaseScanner(ABC):
    """Classe base abstrata para todos os scanners"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.devices = {}  # Dicionário de dispositivos encontrados

    @abstractmethod
    def scan(self, network_cidr: str) -> List[Device]:
        """Executa o scan de descoberta na rede"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica se o scanner está disponível no sistema"""
        pass

    def get_discovered_devices(self) -> List[Device]:
        """Retorna lista de dispositivos descobertos"""
        return list(self.devices.values())

    def _add_or_update_device(self, device: Device) -> Device:
        """Adiciona ou atualiza um dispositivo no dicionário interno"""
        key = device.ip
        if key in self.devices:
            existing = self.devices[key]
            # Mesclar informações
            if device.mac and not existing.mac:
                existing.mac = device.mac
            if device.hostname and not existing.hostname:
                existing.hostname = device.hostname
            if device.os != 'Desconhecido' and existing.os == 'Desconhecido':
                existing.os = device.os
            if device.model != 'Desconhecido' and existing.model == 'Desconhecido':
                existing.model = device.model
            # Adicionar métodos de descoberta
            for method in device.discovery_methods:
                existing.add_discovery_method(method)
            return existing
        else:
            self.devices[key] = device
            return device

    def clear(self):
        """Limpa os dispositivos descobertos"""
        self.devices.clear()
