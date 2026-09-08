"""
API REST para Sistema de Descoberta de Rede
"""

import logging
from flask import Blueprint, jsonify, request
from network_discovery.database.database import NetworkDatabase
from network_discovery.discovery_engine import DiscoveryEngine
from network_discovery.scheduler import ScanScheduler

# Inicializar componentes
db = NetworkDatabase()
discovery_engine = DiscoveryEngine(db)
scheduler = ScanScheduler(db, discovery_engine)

api_bp = Blueprint('network_api', __name__, url_prefix='/api/network')
logger = logging.getLogger(__name__)


# ===== DISPOSITIVOS =====

@api_bp.route('/devices', methods=['GET'])
def get_devices():
    """Lista todos os dispositivos descobertos"""
    try:
        devices = db.get_all_devices()
        return jsonify({
            'success': True,
            'count': len(devices),
            'devices': [d.to_dict() for d in devices]
        })
    except Exception as e:
        logger.error(f'Erro ao listar dispositivos: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/devices/<ip>', methods=['GET'])
def get_device(ip):
    """Obtém informações detalhadas de um dispositivo"""
    try:
        device = db.get_device(ip)
        if not device:
            return jsonify({'success': False, 'error': 'Dispositivo não encontrado'}), 404
        
        # Obter portas e histórico
        ports = db.get_ports_by_device(ip)
        history = db.get_device_history(ip)
        
        return jsonify({
            'success': True,
            'device': device.to_dict(),
            'ports': [p.to_dict() for p in ports],
            'history': [h.to_dict() for h in history]
        })
    except Exception as e:
        logger.error(f'Erro ao obter dispositivo {ip}: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/devices/status/<status>', methods=['GET'])
def get_devices_by_status(status):
    """Lista dispositivos com status específico"""
    try:
        devices = db.get_devices_by_status(status)
        return jsonify({
            'success': True,
            'count': len(devices),
            'devices': [d.to_dict() for d in devices]
        })
    except Exception as e:
        logger.error(f'Erro ao listar dispositivos por status: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ===== CONEXÕES =====

@api_bp.route('/connections', methods=['GET'])
def get_connections():
    """Lista todas as conexões da topologia"""
    try:
        connections = db.get_connections()
        return jsonify({
            'success': True,
            'count': len(connections),
            'connections': [c.to_dict() for c in connections]
        })
    except Exception as e:
        logger.error(f'Erro ao listar conexões: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/connections/<ip>', methods=['GET'])
def get_device_connections(ip):
    """Obtém conexões de um dispositivo"""
    try:
        outgoing, incoming = db.get_connections_for_device(ip)
        return jsonify({
            'success': True,
            'device_ip': ip,
            'outgoing': [c.to_dict() for c in outgoing],
            'incoming': [c.to_dict() for c in incoming]
        })
    except Exception as e:
        logger.error(f'Erro ao obter conexões do dispositivo {ip}: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ===== SCANS =====

@api_bp.route('/scan', methods=['POST'])
def start_scan():
    """Inicia um scan manual"""
    try:
        data = request.get_json() or {}
        network_cidr = data.get('network_cidr')
        
        if not network_cidr:
            return jsonify({
                'success': False,
                'error': 'network_cidr obrigatório'
            }), 400
        
        result = scheduler.trigger_scan(network_cidr)
        return jsonify(result), (200 if result.get('success') else 400)
    
    except Exception as e:
        logger.error(f'Erro ao iniciar scan: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/scan/status', methods=['GET'])
def get_scan_status():
    """Retorna status do scan em execução"""
    try:
        status = scheduler.get_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f'Erro ao obter status do scan: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/scans', methods=['GET'])
def get_scans():
    """Lista últimos scans realizados"""
    try:
        limit = request.args.get('limit', 10, type=int)
        scans = db.get_latest_scans(limit=limit)
        return jsonify({
            'success': True,
            'count': len(scans),
            'scans': [s.to_dict() for s in scans]
        })
    except Exception as e:
        logger.error(f'Erro ao listar scans: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ===== TOPOLOGIA =====

@api_bp.route('/topology', methods=['GET'])
def get_topology():
    """Obtém topologia da rede"""
    try:
        devices = db.get_all_devices()
        connections = db.get_connections()
        
        return jsonify({
            'success': True,
            'nodes': [{
                'id': d.ip,
                'label': d.hostname or d.ip,
                'type': d.device_type.value,
                'status': d.status.value
            } for d in devices],
            'edges': [{
                'source': c.source_ip,
                'target': c.destination_ip,
                'type': c.connection_type.value,
                'confirmed': c.confirmed,
                'confidence': c.confidence
            } for c in connections]
        })
    except Exception as e:
        logger.error(f'Erro ao obter topologia: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/network/status', methods=['GET'])
def get_network_status():
    """Retorna status geral da rede"""
    try:
        status = discovery_engine.get_network_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logger.error(f'Erro ao obter status da rede: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ===== CONFIGURAÇÕES =====

@api_bp.route('/config', methods=['GET'])
def get_config():
    """Retorna configurações do sistema"""
    try:
        config_data = {
            'network_cidr': scheduler.network_cidr,
            'scan_interval_seconds': scheduler.scan_interval,
            'scanners_enabled': {
                'nmap': 'nmap' in discovery_engine.scanners,
                'arp': 'arp' in discovery_engine.scanners,
                'snmp': 'snmp' in discovery_engine.scanners
            },
            'scheduler_running': scheduler.is_running
        }
        return jsonify({'success': True, 'config': config_data})
    except Exception as e:
        logger.error(f'Erro ao obter configurações: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/config', methods=['POST'])
def update_config():
    """Atualiza configurações do sistema"""
    try:
        data = request.get_json() or {}
        
        if 'network_cidr' in data:
            scheduler.network_cidr = data['network_cidr']
        
        if 'scan_interval_seconds' in data:
            scheduler.scan_interval = data['scan_interval_seconds']
        
        if 'scheduler_running' in data:
            if data['scheduler_running'] and not scheduler.is_running:
                scheduler.start()
            elif not data['scheduler_running'] and scheduler.is_running:
                scheduler.stop()
        
        return jsonify({'success': True, 'message': 'Configurações atualizadas'})
    except Exception as e:
        logger.error(f'Erro ao atualizar configurações: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ===== HELTHcheck =====

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check da API"""
    return jsonify({
        'success': True,
        'status': 'ok',
        'scheduler_running': scheduler.is_running,
        'scanners_available': list(discovery_engine.scanners.keys())
    })
