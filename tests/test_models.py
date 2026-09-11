"""
Testes do Módulo de Mapeamento de Rede (sem persistência)
"""

from network_discovery.models import Device, DeviceType
from network_discovery import mapper


class TestDeviceModel:
    def test_device_creation(self):
        device = Device('192.168.1.10', '00:11:22:33:44:55', 'meu-pc')
        assert device.ip == '192.168.1.10'
        assert device.mac == '00:11:22:33:44:55'
        assert device.hostname == 'meu-pc'
        assert device.device_type == DeviceType.UNKNOWN

    def test_device_to_dict(self):
        device = Device('192.168.1.1')
        device.device_type = DeviceType.ROUTER
        device.add_discovery_method('arp')
        d = device.to_dict()
        assert d['ip'] == '192.168.1.1'
        assert d['type'] == 'router'
        assert d['discovery_methods'] == ['arp']


class TestTreeBuilding:
    def _make_devices(self):
        gw = Device('192.168.1.1', '00:00:00:00:00:01')
        gw.device_type = DeviceType.ROUTER

        pc = Device('192.168.1.10', '00:00:00:00:00:02', 'meu-pc')
        pc.device_type = DeviceType.DESKTOP

        return {gw.ip: gw, pc.ip: pc}

    def test_gateway_is_root(self):
        devices = self._make_devices()
        tree = mapper._build_tree(devices, '192.168.1.0/24')
        assert tree['ip'] == '192.168.1.1'
        assert len(tree['children']) == 1
        assert tree['children'][0]['ip'] == '192.168.1.10'

    def test_no_gateway_uses_virtual_root(self):
        pc = Device('10.0.0.5', hostname='pc')
        devices = {pc.ip: pc}
        tree = mapper._build_tree(devices, '10.0.0.0/24')
        assert tree['ip'] is None
        assert tree['type'] == 'network'
        assert len(tree['children']) == 1
