"""
Aplicação Principal - Sistema de Descoberta e Mapeamento de Rede

Executar com:
    python3 app.py

Acesso:
    http://IP_DO_SERVIDOR:5000/rede
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, render_template, jsonify
from network_discovery.api.rede_blueprint import rede_bp
from network_discovery import config

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

app.register_blueprint(rede_bp)


@app.route('/')
def index():
    """Redireciona para o dashboard de rede"""
    return render_template('index.html')


@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'service': 'Network Discovery and Topology Mapping',
        'version': '2.0.0'
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Recurso não encontrado'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Erro interno: {error}')
    return jsonify({'error': 'Erro interno do servidor'}), 500


if __name__ == '__main__':
    logger.info('=' * 60)
    logger.info('Sistema de Mapeamento de Rede')
    logger.info('=' * 60)
    logger.info(f'Rede padrão sugerida: {config.DEFAULT_NETWORK_CIDR}')
    logger.info(f'Nmap habilitado: {config.NMAP_ENABLED}')
    logger.info(f'ARP habilitado: {config.ARP_ENABLED}')
    logger.info('Acesse: http://localhost:5000/rede')
    logger.info('=' * 60)

    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
