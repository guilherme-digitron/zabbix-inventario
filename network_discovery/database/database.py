"""
Banco de Dados SQLite para Sistema de Descoberta de Rede
"""

import sqlite3
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from contextlib import contextmanager
from network_discovery import config
from network_discovery.database.models import (
    Device, Connection, Port, Scan, DeviceHistory, NetworkInterface
)


class NetworkDatabase:
    """Gerenciador de banco de dados SQLite para descoberta de rede"""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or config.DB_PATH
        self.logger = logging.getLogger(__name__)
        self._init_database()

    @contextmanager
    def get_connection(self):
        """Context manager para conexão com banco de dados"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f'Erro na transação do banco: {e}')
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        self.logger.info(f'Inicializando banco de dados em {self.db_path}')
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela de Dispositivos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS devices (
                    ip TEXT PRIMARY KEY,
                    mac TEXT,
                    hostname TEXT,
                    device_type TEXT DEFAULT 'unknown',
                    status TEXT DEFAULT 'unknown',
                    os TEXT,
                    model TEXT,
                    vendor TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    discovery_methods TEXT,
                    metadata TEXT
                )
            ''')
            
            # Tabela de Interfaces
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interfaces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_ip TEXT NOT NULL,
                    interface_name TEXT NOT NULL,
                    ip TEXT,
                    mac TEXT,
                    status TEXT DEFAULT 'up',
                    vlan INTEGER,
                    mtu INTEGER,
                    speed TEXT,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_ip) REFERENCES devices(ip),
                    UNIQUE(device_ip, interface_name)
                )
            ''')
            
            # Tabela de Portas Abertas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_ip TEXT NOT NULL,
                    port_number INTEGER NOT NULL,
                    protocol TEXT DEFAULT 'tcp',
                    state TEXT DEFAULT 'open',
                    service TEXT,
                    version TEXT,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_ip) REFERENCES devices(ip),
                    UNIQUE(device_ip, port_number, protocol)
                )
            ''')
            
            # Tabela de Conexões Entre Dispositivos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_ip TEXT NOT NULL,
                    destination_ip TEXT NOT NULL,
                    source_interface TEXT,
                    destination_interface TEXT,
                    connection_type TEXT DEFAULT 'unknown',
                    discovery_method TEXT,
                    confidence INTEGER DEFAULT 0,
                    confirmed INTEGER DEFAULT 0,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (source_ip) REFERENCES devices(ip),
                    FOREIGN KEY (destination_ip) REFERENCES devices(ip),
                    UNIQUE(source_ip, destination_ip)
                )
            ''')
            
            # Tabela de Scans
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scans (
                    scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    network_cidr TEXT NOT NULL,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    status TEXT DEFAULT 'running',
                    devices_found INTEGER DEFAULT 0,
                    devices_online INTEGER DEFAULT 0,
                    devices_new INTEGER DEFAULT 0,
                    devices_offline INTEGER DEFAULT 0,
                    manual INTEGER DEFAULT 0,
                    methods_used TEXT,
                    notes TEXT
                )
            ''')
            
            # Tabela de Histórico de Dispositivos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS device_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_ip TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    change_type TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    scan_id INTEGER,
                    FOREIGN KEY (device_ip) REFERENCES devices(ip),
                    FOREIGN KEY (scan_id) REFERENCES scans(scan_id)
                )
            ''')
            
            # Índices para performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_device_status ON devices(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_device_type ON devices(device_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_port_device ON ports(device_ip)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_connection_source ON connections(source_ip)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_connection_dest ON connections(destination_ip)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_device ON device_history(device_ip)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_time ON device_history(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scan_time ON scans(start_time)')
            
            self.logger.info('Banco de dados inicializado com sucesso')

    # ===== DISPOSITIVOS =====
    
    def add_device(self, device: Device) -> bool:
        """Adiciona um novo dispositivo ao banco"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO devices 
                    (ip, mac, hostname, device_type, status, os, model, vendor, 
                     first_seen, last_seen, discovery_methods, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    device.ip,
                    device.mac,
                    device.hostname,
                    device.device_type.value,
                    device.status.value,
                    device.os,
                    device.model,
                    device.vendor,
                    device.first_seen,
                    device.last_seen,
                    json.dumps(list(device.discovery_methods)),
                    json.dumps(device.metadata)
                ))
                return True
        except Exception as e:
            self.logger.error(f'Erro ao adicionar dispositivo {device.ip}: {e}')
            return False

    def get_device(self, ip: str) -> Optional[Device]:
        """Obtém um dispositivo do banco"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM devices WHERE ip = ?', (ip,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_device(row)
        except Exception as e:
            self.logger.error(f'Erro ao obter dispositivo {ip}: {e}')
        return None

    def get_all_devices(self) -> List[Device]:
        """Obtém todos os dispositivos do banco"""
        devices = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM devices')
                for row in cursor.fetchall():
                    devices.append(self._row_to_device(row))
        except Exception as e:
            self.logger.error(f'Erro ao obter dispositivos: {e}')
        return devices

    def get_devices_by_status(self, status: str) -> List[Device]:
        """Obtém dispositivos com status específico"""
        devices = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM devices WHERE status = ?', (status,))
                for row in cursor.fetchall():
                    devices.append(self._row_to_device(row))
        except Exception as e:
            self.logger.error(f'Erro ao obter dispositivos por status: {e}')
        return devices

    def update_device_status(self, ip: str, status: str):
        """Atualiza o status de um dispositivo"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE devices SET status = ?, last_seen = CURRENT_TIMESTAMP 
                    WHERE ip = ?
                ''', (status, ip))
        except Exception as e:
            self.logger.error(f'Erro ao atualizar status do dispositivo {ip}: {e}')

    def _row_to_device(self, row) -> Device:
        """Converte uma linha do banco para objeto Device"""
        device = Device(row['ip'], row['mac'], row['hostname'])
        device.device_type = row['device_type']
        device.status = row['status']
        device.os = row['os'] or 'Desconhecido'
        device.model = row['model'] or 'Desconhecido'
        device.vendor = row['vendor'] or 'Desconhecido'
        device.last_seen = datetime.fromisoformat(row['last_seen'])
        device.first_seen = datetime.fromisoformat(row['first_seen'])
        
        if row['discovery_methods']:
            device.discovery_methods = set(json.loads(row['discovery_methods']))
        if row['metadata']:
            device.metadata = json.loads(row['metadata'])
        
        return device

    # ===== PORTAS =====
    
    def add_port(self, port: Port) -> bool:
        """Adiciona uma porta ao banco"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO ports 
                    (device_ip, port_number, protocol, state, service, version)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    port.device_ip,
                    port.port_number,
                    port.protocol,
                    port.state,
                    port.service,
                    port.version
                ))
                return True
        except Exception as e:
            self.logger.error(f'Erro ao adicionar porta: {e}')
            return False

    def get_ports_by_device(self, device_ip: str) -> List[Port]:
        """Obtém portas abertas de um dispositivo"""
        ports = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM ports WHERE device_ip = ? AND state = "open"',
                    (device_ip,)
                )
                for row in cursor.fetchall():
                    port = Port(row['device_ip'], row['port_number'], 
                               row['protocol'], row['state'])
                    port.service = row['service'] or 'Desconhecido'
                    port.version = row['version'] or 'Desconhecido'
                    port.last_seen = datetime.fromisoformat(row['last_seen'])
                    ports.append(port)
        except Exception as e:
            self.logger.error(f'Erro ao obter portas: {e}')
        return ports

    # ===== CONEXÕES =====
    
    def add_connection(self, connection: Connection) -> bool:
        """Adiciona uma conexão entre dispositivos"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO connections 
                    (source_ip, destination_ip, source_interface, destination_interface,
                     connection_type, discovery_method, confidence, confirmed, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    connection.source_ip,
                    connection.destination_ip,
                    connection.source_interface,
                    connection.destination_interface,
                    connection.connection_type.value,
                    connection.discovery_method,
                    connection.confidence,
                    1 if connection.confirmed else 0,
                    json.dumps(connection.metadata)
                ))
                return True
        except Exception as e:
            self.logger.error(f'Erro ao adicionar conexão: {e}')
            return False

    def get_connections(self) -> List[Connection]:
        """Obtém todas as conexões"""
        connections = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM connections')
                for row in cursor.fetchall():
                    conn_obj = Connection(row['source_ip'], row['destination_ip'])
                    conn_obj.source_interface = row['source_interface']
                    conn_obj.destination_interface = row['destination_interface']
                    conn_obj.connection_type = row['connection_type']
                    conn_obj.discovery_method = row['discovery_method']
                    conn_obj.confidence = row['confidence']
                    conn_obj.confirmed = bool(row['confirmed'])
                    conn_obj.last_seen = datetime.fromisoformat(row['last_seen'])
                    connections.append(conn_obj)
        except Exception as e:
            self.logger.error(f'Erro ao obter conexões: {e}')
        return connections

    def get_connections_for_device(self, device_ip: str) -> tuple:
        """Obtém conexões de saída e entrada de um dispositivo"""
        outgoing = []
        incoming = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM connections WHERE source_ip = ?', (device_ip,))
                for row in cursor.fetchall():
                    outgoing.append(Connection(row['source_ip'], row['destination_ip']))
                
                cursor.execute('SELECT * FROM connections WHERE destination_ip = ?', (device_ip,))
                for row in cursor.fetchall():
                    incoming.append(Connection(row['source_ip'], row['destination_ip']))
        except Exception as e:
            self.logger.error(f'Erro ao obter conexões: {e}')
        return outgoing, incoming

    # ===== SCANS =====
    
    def add_scan(self, scan: Scan) -> int:
        """Adiciona um scan ao banco"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO scans 
                    (network_cidr, start_time, status, devices_found, devices_online,
                     devices_new, devices_offline, manual, methods_used, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    scan.network_cidr,
                    scan.start_time,
                    scan.status,
                    scan.devices_found,
                    scan.devices_online,
                    scan.devices_new,
                    scan.devices_offline,
                    1 if scan.manual else 0,
                    json.dumps(scan.methods_used),
                    scan.notes
                ))
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f'Erro ao adicionar scan: {e}')
            return -1

    def update_scan(self, scan_id: int, scan: Scan):
        """Atualiza um scan"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE scans SET end_time = ?, status = ?, devices_found = ?,
                    devices_online = ?, devices_new = ?, devices_offline = ?,
                    methods_used = ?, notes = ?
                    WHERE scan_id = ?
                ''', (
                    scan.end_time,
                    scan.status,
                    scan.devices_found,
                    scan.devices_online,
                    scan.devices_new,
                    scan.devices_offline,
                    json.dumps(scan.methods_used),
                    scan.notes,
                    scan_id
                ))
        except Exception as e:
            self.logger.error(f'Erro ao atualizar scan: {e}')

    def get_latest_scans(self, limit: int = 10) -> List[Scan]:
        """Obtém os últimos scans"""
        scans = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM scans ORDER BY start_time DESC LIMIT ?',
                    (limit,)
                )
                for row in cursor.fetchall():
                    scan = Scan(row['network_cidr'], bool(row['manual']))
                    scan.scan_id = row['scan_id']
                    scan.start_time = datetime.fromisoformat(row['start_time'])
                    if row['end_time']:
                        scan.end_time = datetime.fromisoformat(row['end_time'])
                    scan.status = row['status']
                    scan.devices_found = row['devices_found']
                    scan.devices_online = row['devices_online']
                    scan.devices_new = row['devices_new']
                    scan.devices_offline = row['devices_offline']
                    if row['methods_used']:
                        scan.methods_used = json.loads(row['methods_used'])
                    scan.notes = row['notes'] or ''
                    scans.append(scan)
        except Exception as e:
            self.logger.error(f'Erro ao obter scans: {e}')
        return scans

    # ===== HISTÓRICO =====
    
    def add_history_entry(self, history: DeviceHistory) -> bool:
        """Adiciona entrada ao histórico"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO device_history 
                    (device_ip, timestamp, change_type, old_value, new_value, scan_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    history.device_ip,
                    history.timestamp,
                    history.change_type,
                    history.old_value,
                    history.new_value,
                    history.scan_id
                ))
                return True
        except Exception as e:
            self.logger.error(f'Erro ao adicionar histórico: {e}')
            return False

    def get_device_history(self, device_ip: str, limit: int = 50) -> List[DeviceHistory]:
        """Obtém histórico de um dispositivo"""
        history = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''SELECT * FROM device_history WHERE device_ip = ? 
                       ORDER BY timestamp DESC LIMIT ?''',
                    (device_ip, limit)
                )
                for row in cursor.fetchall():
                    hist = DeviceHistory(
                        row['device_ip'],
                        row['change_type'],
                        row['old_value'],
                        row['new_value']
                    )
                    hist.timestamp = datetime.fromisoformat(row['timestamp'])
                    hist.scan_id = row['scan_id']
                    history.append(hist)
        except Exception as e:
            self.logger.error(f'Erro ao obter histórico: {e}')
        return history
