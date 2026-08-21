import time
from flask import Blueprint, jsonify, request, current_app
from .services.discovery_manager import DiscoveryManager

api_bp = Blueprint("rede_api", __name__, url_prefix="/api/rede")

# Usaremos um DiscoveryManager singleton por processo (muito leve)
dm = DiscoveryManager.get_instance()

@api_bp.route("/status")
def status():
    s = dm.status()
    return jsonify(s)

@api_bp.route("/dispositivos")
def dispositivos():
    devices = dm.get_devices()
    return jsonify(devices)

@api_bp.route("/topologia")
def topologia():
    topo = dm.get_topology()
    return jsonify(topo)

@api_bp.route("/discover", methods=["POST"])
def discover():
    # Inicia descoberta em background (não bloqueia)
    dm.start_discovery()
    return jsonify({"result": "started"}), 202

@api_bp.route("/device/<int:device_id>")
def device(device_id):
    d = dm.get_device(device_id)
    if not d:
        return jsonify({"error": "not found"}), 404
    return jsonify(d)
