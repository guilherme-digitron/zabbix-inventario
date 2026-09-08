"""
Motor de Correlação de Dados
Combina informações de múltiplas fontes para criar uma visão consolidada da rede
"""

import logging
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
from network_discovery.database.models import Device, Connection, ConnectionType, DiscoveryMethod
from network_discovery.database.database import NetworkDatabase


class CorrelationEngine:
    """Engine para correlacionar dados de descoberta"""
    
    def __init__(self, db: NetworkDatabase):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.devices = {}
        self.connections = []

    def correlate_devices(self, devices: List[Device]) -> List[Device]:
        """Correlaciona dispositivos de múltiplas fontes
        
        Mescla informações de dispositivos duplicados (mesmo IP ou MAC)
        e enriquece com dados do banco de dados anterior
        """
        self.logger.info(f'Correlacionando {len(devices)} dispositivos')
        self.devices.clear()
        
        # Primeiro, agrupar por IP
        devices_by_ip = {d.ip: d for d in devices}
        
        # Depois, tentar consolidar com MAC
        devices_by_mac = defaultdict(list)
        for device in devices:
            if device.mac:
                devices_by_mac[device.mac].append(device)
        
        # Processar cada dispositivo
        processed_ips = set()
        for ip, device in devices_by_ip.items():
            if ip in processed_ips:
                continue
            
            # Obter informações do banco anterior
            old_device = self.db.get_device(ip)
            
            if old_device:
                # Mesclar com informações do banco
                merged = self._merge_devices(device, old_device)
                self.devices[ip] = merged
            else:
                # Novo dispositivo
                self.devices[ip] = device
            
            processed_ips.add(ip)
        
        return list(self.devices.values())

    def _merge_devices(self, new_device: Device, old_device: Device) -> Device:
        """Mescla informações de dois dispositivos"""
        # Manter o dispositivo novo como base
        merged = new_device
        
        # Preencher informações faltantes do antigo
        if not merged.mac and old_device.mac:
            merged.mac = old_device.mac
        if not merged.hostname and old_device.hostname:
            merged.hostname = old_device.hostname
        if merged.os == 'Desconhecido' and old_device.os != 'Desconhecido':
            merged.os = old_device.os
        if merged.model == 'Desconhecido' and old_device.model != 'Desconhecido':
            merged.model = old_device.model
        if merged.vendor == 'Desconhecido' and old_device.vendor != 'Desconhecido':
            merged.vendor = old_device.vendor
        
        # Manter primeiro aparecimento
        if old_device.first_seen < merged.first_seen:
            merged.first_seen = old_device.first_seen
        
        # Combinar métodos de descoberta
        for method in old_device.discovery_methods:
            merged.add_discovery_method(method)
        
        return merged

    def infer_connections(self) -> List[Connection]:
        """Infere conexões entre dispositivos baseado em diferentes critérios"""
        self.logger.info('Inferindo conexões entre dispositivos')
        self.connections.clear()
        
        # 1. Detectar possível gateway (roteador com portas abertas 22, 80, 443)
        gateways = self._identify_gateways()
        
        # 2. Detectar switches gerenciáveis (com SNMP, telnet, SSH)
        switches = self._identify_switches()
        
        # 3. Detectar access points (portas de gerenciamento, WebUI)
        access_points = self._identify_access_points()
        
        # 4. Conectar dispositivos ao gateway (assume topologia em árvore)
        if gateways:
            self._connect_to_gateway(gateways[0])
        
        # 5. Conectar dispositivos móveis/clientes ao AP
        self._connect_to_access_points(access_points)
        
        return self.connections

    def _identify_gateways(self) -> List[str]:
        """Identifica possíveis roteadores/gateways"""
        gateways = []
        
        for ip, device in self.devices.items():
            # Heurísticas para identificar gateway
            gateway_score = 0
            
            # Ter IPs terminando em .1 é comum para gateway
            if ip.endswith('.1'):
                gateway_score += 30
            
            # Ter porta SSH aberta é comum
            if any(p.get('port') == 22 for p in device.open_ports):
                gateway_score += 15
            
            # Ter porta HTTP/HTTPS aberta é comum para admin
            if any(p.get('port') in [80, 443, 8080, 8443] for p in device.open_ports):
                gateway_score += 15
            
            # Ós tipo router
            if device.device_type.value == 'router':
                gateway_score += 50
            
            # Se score > 30, é possível gateway
            if gateway_score >= 30:
                gateways.append(ip)
        
        self.logger.info(f'Identificados {len(gateways)} possíveis gateways: {gateways}')
        return gateways

    def _identify_switches(self) -> List[str]:
        """Identifica possíveis switches gerenciáveis"""
        switches = []
        
        for ip, device in self.devices.items():
            # Heurísticas para switch
            switch_score = 0
            
            # Tipo device = switch
            if device.device_type.value == 'switch':
                switch_score += 50
            
            # Porta SNMP aberta (161)
            if any(p.get('port') == 161 for p in device.open_ports):
                switch_score += 25
            
            # Hostname com "switch" ou "sw"
            if device.hostname and ('switch' in device.hostname.lower() or 'sw' in device.hostname.lower()):
                switch_score += 20
            
            if switch_score >= 30:
                switches.append(ip)
        
        self.logger.info(f'Identificados {len(switches)} possíveis switches: {switches}')
        return switches

    def _identify_access_points(self) -> List[str]:
        """Identifica possíveis access points WiFi"""
        aps = []
        
        for ip, device in self.devices.items():
            ap_score = 0
            
            if device.device_type.value == 'access_point':
                ap_score += 50
            
            # Hostname com "ap" ou "wifi" ou "wireless"
            if device.hostname:
                hostname_lower = device.hostname.lower()
                if any(x in hostname_lower for x in ['ap', 'wifi', 'wireless', 'access']):
                    ap_score += 20
            
            # Portas típicas de AP (80, 443, 8080)
            if any(p.get('port') in [80, 443, 8080] for p in device.open_ports):
                ap_score += 10
            
            if ap_score >= 30:
                aps.append(ip)
        
        return aps

    def _connect_to_gateway(self, gateway_ip: str):
        """Conecta dispositivos ao gateway (assume todos estão conectados diretamente)"""
        self.logger.info(f'Conectando dispositivos ao gateway {gateway_ip}')
        
        gateway_device = self.devices.get(gateway_ip)
        if not gateway_device:
            return
        
        for ip, device in self.devices.items():
            if ip == gateway_ip:
                continue
            
            # Não conectar switches ao gateway como clientes
            if device.device_type.value == 'switch':
                continue
            
            # Criar conexão inferida
            conn = Connection(ip, gateway_ip)
            conn.connection_type = ConnectionType.INFERRED
            conn.discovery_method = 'topology_inference'
            
            # Aumentar confiança se o dispositivo tem IP na mesma rede
            if self._same_network(ip, gateway_ip):
                conn.confidence = 75
            else:
                conn.confidence = 40
            
            self.connections.append(conn)

    def _connect_to_access_points(self, access_points: List[str]):
        """Conecta smartphones/tablets aos APs"""
        for ap_ip in access_points:
            ap_device = self.devices.get(ap_ip)
            if not ap_device:
                continue
            
            # Procurar por smartphones próximos
            for ip, device in self.devices.items():
                if ip == ap_ip:
                    continue
                
                if device.device_type.value in ['smartphone', 'tablet', 'iot']:
                    conn = Connection(ip, ap_ip)
                    conn.connection_type = ConnectionType.INFERRED
                    conn.discovery_method = 'device_type_inference'
                    conn.confidence = 60
                    self.connections.append(conn)

    def _same_network(self, ip1: str, ip2: str, netmask: str = '255.255.255.0') -> bool:
        """Verifica se dois IPs estão na mesma rede"""
        try:
            from ipaddress import ip_address, IPv4Network
            
            # Tentar com netmask /24 (classe C)
            network = IPv4Network(f'{ip1}/24', strict=False)
            return ip_address(ip2) in network
        except Exception:
            return False

    def detect_device_type_changes(self) -> List[Tuple[str, str, str]]:
        """Detecta mudanças no tipo de dispositivo"""
        changes = []
        
        for ip, device in self.devices.items():
            old_device = self.db.get_device(ip)
            if old_device and old_device.device_type != device.device_type:
                changes.append((ip, old_device.device_type.value, device.device_type.value))
        
        return changes

    def detect_offline_devices(self, max_age_hours: int = 24) -> List[str]:
        """Detecta dispositivos que ficaram offline"""
        offline = []
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        all_devices = self.db.get_all_devices()
        current_ips = set(self.devices.keys())
        
        for device in all_devices:
            if device.ip not in current_ips and device.last_seen > cutoff_time:
                offline.append(device.ip)
        
        return offline
