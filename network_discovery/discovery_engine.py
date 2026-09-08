"""
Motor de Descoberta
Orquestra os diferentes scanners e coordena a coleta de dados
"""

import logging
import concurrent.futures
from typing import List, Dict, Optional
from datetime import datetime
from network_discovery.database.models import (
    Device, Scan, DiscoveryMethod, DeviceHistory, DeviceStatus
)
from network_discovery.database.database import NetworkDatabase
from network_discovery.scanner.nmap_scanner import NmapScanner
from network_discovery.scanner.arp_scanner import ARPScanner
from network_discovery.scanner.snmp_scanner import SNMPScanner
from network_discovery.topology.correlation import CorrelationEngine
from network_discovery.topology.topology_engine import TopologyEngine
from network_discovery.topology.graph_generator import GraphGenerator
from network_discovery import config


class DiscoveryEngine:
    """Engine principal de descoberta de rede"""
    
    def __init__(self, db: NetworkDatabase):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.scanners = {}
        self.current_scan = None
        self.scan_id = None
        
        # Inicializar scanners
        self._init_scanners()
    
    def _init_scanners(self):
        """Inicializa os scanners disponíveis"""
        self.logger.info('Inicializando scanners de descoberta')
        
        if config.NMAP_ENABLED:
            nmap_scanner = NmapScanner()
            if nmap_scanner.is_available():
                self.scanners['nmap'] = nmap_scanner
                self.logger.info('Nmap scanner habilitado')
            else:
                self.logger.warning('Nmap não disponível no sistema')
        
        if config.ARP_ENABLED:
            arp_scanner = ARPScanner()
            if arp_scanner.is_available():
                self.scanners['arp'] = arp_scanner
                self.logger.info('ARP scanner habilitado')
            else:
                self.logger.warning('ARP não disponível no sistema')
        
        if config.SNMP_ENABLED:
            snmp_scanner = SNMPScanner()
            if snmp_scanner.is_available():
                self.scanners['snmp'] = snmp_scanner
                self.logger.info('SNMP scanner habilitado')
            else:
                self.logger.warning('SNMP não disponível no sistema')
    
    def discover_network(self, network_cidr: str, manual: bool = False) -> Dict:
        """Executa descoberta completa da rede
        
        Args:
            network_cidr: CIDR da rede (ex: 192.168.1.0/24)
            manual: Se True, indica descoberta manual pelo usuário
        
        Returns:
            Dict com resultados da descoberta
        """
        self.logger.info(f'Iniciando descoberta de {network_cidr} (manual={manual})')
        
        # Criar novo scan
        self.current_scan = Scan(network_cidr, manual=manual)
        self.scan_id = self.db.add_scan(self.current_scan)
        self.current_scan.scan_id = self.scan_id
        
        try:
            # 1. Executar scanners em paralelo
            all_devices = self._run_scanners(network_cidr)
            self.logger.info(f'Scanners encontraram {len(all_devices)} dispositivos')
            
            # 2. Correlacionar dados
            correlation_engine = CorrelationEngine(self.db)
            correlated_devices = correlation_engine.correlate_devices(all_devices)
            self.logger.info(f'Após correlação: {len(correlated_devices)} dispositivos')
            
            # 3. Detectar mudanças e atualizar banco
            self._detect_changes(correlated_devices)
            
            # 4. Construir topologia
            topology_engine = TopologyEngine(self.db)
            connections = correlation_engine.infer_connections()
            topology_data = topology_engine.build_topology(correlated_devices, connections)
            
            # 5. Salvar dispositivos e conexões
            self._save_devices_and_connections(correlated_devices, connections)
            
            # 6. Gerar gráfico SVG
            graph_gen = GraphGenerator()
            svg_map = graph_gen.generate_svg(topology_data)
            
            # 7. Atualizar scan com resultados
            self.current_scan.status = 'completed'
            self.current_scan.end_time = datetime.now()
            self.current_scan.devices_found = len(correlated_devices)
            self.current_scan.devices_online = sum(1 for d in correlated_devices 
                                                   if d.status == DeviceStatus.ONLINE)
            self.current_scan.methods_used = list(self.scanners.keys())
            
            self.db.update_scan(self.scan_id, self.current_scan)
            
            self.logger.info(f'Descoberta concluída: {len(correlated_devices)} dispositivos encontrados')
            
            return {
                'success': True,
                'scan_id': self.scan_id,
                'devices': [d.to_dict() for d in correlated_devices],
                'connections': [c.to_dict() for c in connections],
                'topology': topology_data,
                'svg_map': svg_map,
                'summary': {
                    'total_devices': len(correlated_devices),
                    'online_devices': self.current_scan.devices_online,
                    'offline_devices': self.current_scan.devices_offline,
                    'new_devices': self.current_scan.devices_new,
                    'duration_seconds': (self.current_scan.end_time - self.current_scan.start_time).total_seconds()
                }
            }
        
        except Exception as e:
            self.logger.error(f'Erro durante descoberta: {e}', exc_info=True)
            self.current_scan.status = 'failed'
            self.current_scan.notes = str(e)
            self.db.update_scan(self.scan_id, self.current_scan)
            
            return {
                'success': False,
                'scan_id': self.scan_id,
                'error': str(e)
            }
    
    def _run_scanners(self, network_cidr: str) -> List[Device]:
        """Executa todos os scanners em paralelo
        
        BUG FIX:
        - Removido timeout curto artificial (DISCOVERY_TIMEOUT=30s) que causava
          TimeoutExpired/TimeoutError ao executar 3 varreduras nmap sequenciais
        - Mudado de concurrent.futures.TimeoutExpired (não existe) para 
          concurrent.futures.TimeoutError (correto para ThreadPoolExecutor)
        - Cada scanner tem seu próprio timeout interno (NMAP_TIMEOUT=300s)
        """
        self.logger.info(f'Executando {len(self.scanners)} scanners em paralelo')
        
        all_devices = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.scanners)) as executor:
            futures = {}
            
            for scanner_name, scanner in self.scanners.items():
                future = executor.submit(scanner.scan, network_cidr)
                futures[future] = scanner_name
            
            for future in concurrent.futures.as_completed(futures):
                scanner_name = futures[future]
                try:
                    # Remover timeout curto - deixar cada scanner controlar seu próprio timeout
                    devices = future.result()
                    
                    for device in devices:
                        if device.ip not in all_devices:
                            all_devices[device.ip] = device
                        else:
                            # Mesclar informações
                            existing = all_devices[device.ip]
                            if device.mac and not existing.mac:
                                existing.mac = device.mac
                            if device.hostname and not existing.hostname:
                                existing.hostname = device.hostname
                            for method in device.discovery_methods:
                                existing.add_discovery_method(method)
                    
                    self.logger.info(f'{scanner_name}: {len(devices)} dispositivos')
                
                # CORREÇÃO: usar concurrent.futures.TimeoutError (não TimeoutExpired)
                except concurrent.futures.TimeoutError:
                    self.logger.warning(f'{scanner_name} timeout')
                except Exception as e:
                    self.logger.error(f'Erro em {scanner_name}: {e}', exc_info=True)
        
        return list(all_devices.values())
    
    def _detect_changes(self, new_devices: List[Device]):
        """Detecta mudanças em relação à descoberta anterior"""
        old_devices = {d.ip: d for d in self.db.get_all_devices()}
        new_devices_dict = {d.ip: d for d in new_devices}
        
        # Dispositivos novos
        for ip in new_devices_dict:
            if ip not in old_devices:
                self.current_scan.devices_new += 1
                history = DeviceHistory(ip, 'new', None, ip)
                history.scan_id = self.scan_id
                self.db.add_history_entry(history)
                self.logger.info(f'Novo dispositivo: {ip}')
        
        # Dispositivos que ficaram offline
        for ip in old_devices:
            if ip not in new_devices_dict:
                self.current_scan.devices_offline += 1
                history = DeviceHistory(ip, 'offline', 'online', 'offline')
                history.scan_id = self.scan_id
                self.db.add_history_entry(history)
                self.logger.info(f'Dispositivo offline: {ip}')
        
        # Detectar mudanças em dispositivos existentes
        for ip, new_device in new_devices_dict.items():
            if ip in old_devices:
                old_device = old_devices[ip]
                
                # Mudança de MAC
                if new_device.mac != old_device.mac:
                    history = DeviceHistory(ip, 'mac_change', old_device.mac, new_device.mac)
                    history.scan_id = self.scan_id
                    self.db.add_history_entry(history)
                    self.logger.warning(f'MAC alterado para {ip}: {old_device.mac} -> {new_device.mac}')
                
                # Mudança de hostname
                if new_device.hostname != old_device.hostname:
                    history = DeviceHistory(ip, 'hostname_change', old_device.hostname, new_device.hostname)
                    history.scan_id = self.scan_id
                    self.db.add_history_entry(history)
                    self.logger.info(f'Hostname alterado para {ip}: {old_device.hostname} -> {new_device.hostname}')
    
    def _save_devices_and_connections(self, devices: List[Device], connections: List):
        """Salva dispositivos e conexões no banco"""
        for device in devices:
            self.db.add_device(device)
        
        for connection in connections:
            self.db.add_connection(connection)
    
    def get_scan_status(self, scan_id: int) -> Dict:
        """Retorna status de um scan"""
        if self.scan_id == scan_id and self.current_scan:
            return self.current_scan.to_dict()
        return {}
    
    def get_network_status(self) -> Dict:
        """Retorna status geral da rede"""
        devices = self.db.get_all_devices()
        online = sum(1 for d in devices if d.status == DeviceStatus.ONLINE)
        offline = sum(1 for d in devices if d.status == DeviceStatus.OFFLINE)
        unknown = sum(1 for d in devices if d.status == DeviceStatus.UNKNOWN)
        
        scans = self.db.get_latest_scans(limit=1)
        last_scan = scans[0] if scans else None
        
        return {
            'total_devices': len(devices),
            'online_devices': online,
            'offline_devices': offline,
            'unknown_devices': unknown,
            'last_scan': last_scan.to_dict() if last_scan else None,
            'scanners_available': list(self.scanners.keys())
        }
