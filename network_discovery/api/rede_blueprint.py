"""
Blueprint da Interface de Mapeamento de Rede (sem persistência)
"""

import logging
from flask import Blueprint, render_template, jsonify, request

from network_discovery import mapper, config

rede_bp = Blueprint('rede', __name__, url_prefix='/rede')
logger = logging.getLogger(__name__)


@rede_bp.route('/', methods=['GET'])
def rede_dashboard():
    """Página única: executar mapeamento e ver o resultado em árvore"""
    return render_template('rede/dashboard.html', default_network=mapper.get_local_network())


@rede_bp.route('/api/scan', methods=['POST'])
def rede_scan():
    """Executa o mapeamento de rede sob demanda e retorna a árvore de topologia"""
    data = request.get_json(silent=True) or {}
    network_cidr = data.get('network_cidr') or config.DEFAULT_NETWORK_CIDR

    try:
        result = mapper.run_mapping(network_cidr)
    except Exception as e:
        logger.error(f'Erro ao executar mapeamento: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code
