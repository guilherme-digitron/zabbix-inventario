"""
Blueprint para a Interface de Rede
"""

from flask import Blueprint, render_template, jsonify

rede_bp = Blueprint('rede', __name__, url_prefix='/rede')


@rede_bp.route('/', methods=['GET'])
def rede_dashboard():
    """Página principal do painel de rede"""
    return render_template('rede/dashboard.html')


@rede_bp.route('/detalhes/<ip>', methods=['GET'])
def rede_device_details(ip):
    """Página de detalhes do dispositivo"""
    return render_template('rede/device_details.html', device_ip=ip)


@rede_bp.route('/configuracoes', methods=['GET'])
def rede_settings():
    """Página de configurações"""
    return render_template('rede/settings.html')


@rede_bp.route('/historico', methods=['GET'])
def rede_history():
    """Página de histórico"""
    return render_template('rede/history.html')
