"""
Testos Unitários para o Sistema de Descoberta de Rede
"""

import pytest
import tempfile
from pathlib import Path

from network_discovery.database.models import Device, Connection, DeviceType, DeviceStatus
from network_discovery.database.database import NetworkDatabase


class TestDeviceModel:
    """Testes para o modelo Device"""
    
    def test_device_creation(self):
        """Testa criação básica de dispositivo"""
        device = Device('192.168.1.10', '00:11:22:33:44:55', 'computer')
        assert device.ip == '192.168.1.10'
        assert device.mac == '00:11:22:33:44:55'
        assert device.hostname == 'computer'
    
    def test_device_to_dict(self):
        """Testa conversão de dispositivo para dicionário"""
        device = Device('192.168.1.10')
        device.device_type = DeviceType.DESKTOP
        device.status = DeviceStatus.ONLINE
        
        d = device.to_dict()
        assert d['ip'] == '192.168.1.10'
        assert d['type'] == 'desktop'
        assert d['status'] == 'online'


class TestNetworkDatabase:
    """Testes para o banco de dados"""
    
    @pytest.fixture
    def temp_db(self):
        """Cria um banco de dados temporário para testes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'test.db'
            db = NetworkDatabase(db_path)
            yield db
    
    def test_add_device(self, temp_db):
        """Testa adicionar dispositivo ao banco"""
        device = Device('192.168.1.10', '00:11:22:33:44:55')
        device.device_type = DeviceType.DESKTOP
        
        result = temp_db.add_device(device)
        assert result is True
        
        retrieved = temp_db.get_device('192.168.1.10')
        assert retrieved is not None
        assert retrieved.ip == '192.168.1.10'
    
    def test_get_all_devices(self, temp_db):
        """Testa obter todos os dispositivos"""
        for i in range(3):
            device = Device(f'192.168.1.{10+i}')
            temp_db.add_device(device)
        
        devices = temp_db.get_all_devices()
        assert len(devices) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
