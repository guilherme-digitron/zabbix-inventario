"""
Motor de Topologia
Gera e correlaciona conexões entre dispositivos
"""

import logging
from typing import List, Dict, Set
from collections import defaultdict
from network_discovery.database.models import Device, Connection, ConnectionType
from network_discovery.database.database import NetworkDatabase


class TopologyEngine:
    """Engine para gerar topologia da rede"""
    
    def __init__(self, db: NetworkDatabase):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.devices = {}
        self.connections = []
        self.topology_graph = {}  # Gráfico de topologia

    def build_topology(self, devices: List[Device], connections: List[Connection]) -> Dict:
        """Constrói a topologia da rede"""
        self.logger.info('Construindo topologia da rede')
        self.devices = {d.ip: d for d in devices}
        self.connections = connections
        
        # Construir grafo de conexões
        self._build_graph()
        
        # Identificar níveis (distancia do core)
        self._identify_levels()
        
        # Validar topologia
        self._validate_topology()
        
        return self.get_topology_data()

    def _build_graph(self):
        """Constrói grafo de conexões"""
        self.topology_graph = defaultdict(list)
        
        for conn in self.connections:
            self.topology_graph[conn.source_ip].append({
                'destination': conn.destination_ip,
                'type': conn.connection_type.value,
                'confidence': conn.confidence,
                'confirmed': conn.confirmed
            })

    def _identify_levels(self):
        """Identifica nível de cada dispositivo na topologia"""
        levels = {}
        visited = set()
        
        # BFS do gateway (nível 0)
        gateways = [ip for ip, d in self.devices.items() 
                   if d.device_type.value == 'router']
        
        if not gateways:
            # Se não houver gateway, usar como raiz o dispositivo com mais conexões
            gateways = [max(self.devices.keys(), 
                           key=lambda ip: len(self.topology_graph[ip]))]
        
        queue = [(gw, 0) for gw in gateways]
        
        while queue:
            current, level = queue.pop(0)
            
            if current in visited:
                continue
            
            visited.add(current)
            levels[current] = level
            
            for neighbor_info in self.topology_graph[current]:
                neighbor = neighbor_info['destination']
                if neighbor not in visited:
                    queue.append((neighbor, level + 1))
        
        # Atribuir níveis aos dispositivos
        for ip, device in self.devices.items():
            if ip in levels:
                device.metadata['topology_level'] = levels[ip]
            else:
                device.metadata['topology_level'] = -1  # Não conectado

    def _validate_topology(self):
        """Valida a topologia para garantir consistência"""
        # Verificar se há loops (seráo marcados como conexões com baixa confiança)
        self.logger.debug('Validando topologia...')
        
        invalid_connections = []
        for conn in self.connections:
            # Verificar se ambos os dispositivos existem
            if conn.source_ip not in self.devices or conn.destination_ip not in self.devices:
                invalid_connections.append(conn)
            
            # Verificar conexões loop (mesmo dispositivo)
            if conn.source_ip == conn.destination_ip:
                invalid_connections.append(conn)
        
        for conn in invalid_connections:
            self.connections.remove(conn)
            self.logger.warning(f'Conexão inválida removida: {conn.source_ip} -> {conn.destination_ip}')

    def get_topology_data(self) -> Dict:
        """Retorna dados da topologia em formato estruturado"""
        return {
            'nodes': [
                {
                    'id': device.ip,
                    'label': device.hostname or device.ip,
                    'type': device.device_type.value,
                    'status': device.status.value,
                    'level': device.metadata.get('topology_level', -1),
                }
                for device in self.devices.values()
            ],
            'edges': [
                {
                    'source': conn.source_ip,
                    'target': conn.destination_ip,
                    'type': conn.connection_type.value,
                    'confirmed': conn.confirmed,
                    'confidence': conn.confidence,
                }
                for conn in self.connections
            ],
            'stats': self._calculate_stats()
        }

    def _calculate_stats(self) -> Dict:
        """Calcula estatísticas da topologia"""
        return {
            'total_devices': len(self.devices),
            'total_connections': len(self.connections),
            'confirmed_connections': sum(1 for c in self.connections if c.confirmed),
            'inferred_connections': sum(1 for c in self.connections if not c.confirmed),
            'device_types': self._count_device_types(),
            'online_devices': sum(1 for d in self.devices.values() if d.status.value == 'online'),
            'offline_devices': sum(1 for d in self.devices.values() if d.status.value == 'offline'),
        }

    def _count_device_types(self) -> Dict[str, int]:
        """Conta quantos dispositivos de cada tipo"""
        counts = defaultdict(int)
        for device in self.devices.values():
            counts[device.device_type.value] += 1
        return dict(counts)

    def get_device_info(self, device_ip: str) -> Dict:
        """Retorna informações detalhadas de um dispositivo"""
        device = self.devices.get(device_ip)
        if not device:
            return {}
        
        # Obter conexões
        outgoing = []
        incoming = []
        
        for conn in self.connections:
            if conn.source_ip == device_ip:
                outgoing.append({
                    'destination': conn.destination_ip,
                    'destination_hostname': self.devices.get(conn.destination_ip, {}).hostname,
                    'type': conn.connection_type.value,
                    'confirmed': conn.confirmed,
                    'confidence': conn.confidence,
                })
            elif conn.destination_ip == device_ip:
                incoming.append({
                    'source': conn.source_ip,
                    'source_hostname': self.devices.get(conn.source_ip, {}).hostname,
                    'type': conn.connection_type.value,
                    'confirmed': conn.confirmed,
                    'confidence': conn.confidence,
                })
        
        return {
            'ip': device.ip,
            'hostname': device.hostname or 'Desconhecido',
            'mac': device.mac or 'Desconhecido',
            'type': device.device_type.value,
            'status': device.status.value,
            'os': device.os,
            'model': device.model,
            'vendor': device.vendor,
            'open_ports': device.open_ports,
            'first_seen': device.first_seen.isoformat(),
            'last_seen': device.last_seen.isoformat(),
            'discovery_methods': list(device.discovery_methods),
            'connections_outgoing': outgoing,
            'connections_incoming': incoming,
            'topology_level': device.metadata.get('topology_level', -1),
        }
