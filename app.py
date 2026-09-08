"""
Aplicação Principal - Sistema de Descoberta e Mapeamento de Rede

Executar com:
    python3 app.py

Acesso:
    http://IP_DO_SERVIDOR:5000/rede
"""

import os
import sys
import logging
from pathlib import Path

# Adicionar diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, render_template, jsonify
from network_discovery.database.database import NetworkDatabase
from network_discovery.api.api import api_bp
from network_discovery.api.rede_blueprint import rede_bp
from network_discovery import config

# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Criar aplicação Flask
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Inicializar banco de dados
db = NetworkDatabase()
logger.info(f'Banco de dados inicializado: {config.DB_PATH}')

# Registrar blueprints
app.register_blueprint(api_bp)
app.register_blueprint(rede_bp)

# Rota raiz
@app.route('/')
def index():
    """Redireciona para o dashboard de rede"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check da aplicação"""
    return jsonify({
        'status': 'ok',
        'service': 'Network Discovery and Topology Mapping',
        'version': '1.0.0'
    })

# Tratamento de erros
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Recurso não encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Erro interno: {error}')
    return jsonify({'error': 'Erro interno do servidor'}), 500

# Antes de executar a aplicação
if __name__ == '__main__':
    logger.info('='*60)
    logger.info('Sistema de Descoberta e Mapeamento de Rede')
    logger.info('='*60)
    logger.info(f'Rede configurada: {config.DEFAULT_NETWORK_CIDR}')
    logger.info(f'Intervalo de scan: {config.DEFAULT_SCAN_INTERVAL}s')
    logger.info(f'Scanners habilitados:')
    logger.info(f'  - Nmap: {config.NMAP_ENABLED}')
    logger.info(f'  - ARP: {config.ARP_ENABLED}')
    logger.info(f'  - SNMP: {config.SNMP_ENABLED}')
    logger.info(f'Acesse: http://localhost:5000/rede')
    logger.info('='*60)
    
    # Executar aplicação
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False
    )
