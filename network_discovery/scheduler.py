"""
Coordenador de Scans Agendados
Gerencia execução automática de scans
"""

import logging
import threading
import time
from typing import Dict, Optional
from datetime import datetime
from network_discovery.discovery_engine import DiscoveryEngine
from network_discovery.database.database import NetworkDatabase
from network_discovery import config


class ScanScheduler:
    """Coordena scans automáticos"""
    
    def __init__(self, db: NetworkDatabase, discovery_engine: DiscoveryEngine):
        self.db = db
        self.discovery_engine = discovery_engine
        self.logger = logging.getLogger(__name__)
        
        self.is_running = False
        self.scheduler_thread = None
        self.network_cidr = config.DEFAULT_NETWORK_CIDR
        self.scan_interval = config.DEFAULT_SCAN_INTERVAL
        self.last_scan_time = None
        self.current_scan_running = False
    
    def start(self, network_cidr: str = None, interval_seconds: int = None):
        """Inicia o agendador de scans"""
        if self.is_running:
            self.logger.warning('Scheduler já está executando')
            return
        
        if network_cidr:
            self.network_cidr = network_cidr
        if interval_seconds:
            self.scan_interval = interval_seconds
        
        self.logger.info(f'Iniciando scheduler: rede={self.network_cidr}, intervalo={self.scan_interval}s')
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
    
    def stop(self):
        """Para o agendador"""
        self.logger.info('Parando scheduler')
        self.is_running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
    
    def _scheduler_loop(self):
        """Loop principal do agendador"""
        self.logger.info('Scheduler iniciado')
        
        while self.is_running:
            try:
                # Verificar se é hora de executar scan
                if self.last_scan_time is None or \
                   (time.time() - self.last_scan_time) >= self.scan_interval:
                    
                    if not self.current_scan_running:
                        self.logger.info(f'Executando scan agendado da rede {self.network_cidr}')
                        self.current_scan_running = True
                        
                        try:
                            self.discovery_engine.discover_network(self.network_cidr, manual=False)
                            self.last_scan_time = time.time()
                        except Exception as e:
                            self.logger.error(f'Erro no scan agendado: {e}')
                        finally:
                            self.current_scan_running = False
                
                # Aguardar 10 segundos antes de verificar novamente
                time.sleep(10)
            
            except Exception as e:
                self.logger.error(f'Erro no scheduler loop: {e}')
                time.sleep(60)
    
    def trigger_scan(self, network_cidr: str = None) -> Dict:
        """Executa um scan manual imediatamente"""
        if self.current_scan_running:
            return {'success': False, 'error': 'Scan já em execução'}
        
        cidr = network_cidr or self.network_cidr
        self.logger.info(f'Executando scan manual: {cidr}')
        
        self.current_scan_running = True
        try:
            result = self.discovery_engine.discover_network(cidr, manual=True)
            self.last_scan_time = time.time()
            return result
        except Exception as e:
            self.logger.error(f'Erro no scan manual: {e}')
            return {'success': False, 'error': str(e)}
        finally:
            self.current_scan_running = False
    
    def is_scan_running(self) -> bool:
        """Verifica se um scan está em execução"""
        return self.current_scan_running
    
    def get_status(self) -> Dict:
        """Retorna status do scheduler"""
        return {
            'running': self.is_running,
            'network_cidr': self.network_cidr,
            'scan_interval_seconds': self.scan_interval,
            'last_scan_time': self.last_scan_time,
            'scan_in_progress': self.current_scan_running,
            'network_status': self.discovery_engine.get_network_status()
        }
