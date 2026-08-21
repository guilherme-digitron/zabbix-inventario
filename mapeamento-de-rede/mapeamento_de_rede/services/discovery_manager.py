import threading
import time
from ..discovery import network as net
from ..discovery import arp as arpmod
from ..discovery import nmap_scan
from ..discovery import topology as topo_mod
from ..database.database import Database
import datetime

class DiscoveryManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.db = Database.get()
        self._running = False
        self._thread = None
        self._status = {"running": False, "last_run": None, "devices": 0, "connections": 0, "progress": 0}

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = DiscoveryManager()
            return cls._instance

    def status(self):
        return self._status

    def start_discovery(self):
        if self._running:
            return False
        self._thread = threading.Thread(target=self._discover_background, daemon=True)
        self._thread.start()
        return True

    def _discover_background(self):
        self._running = True
        self._status.update({"running": True, "progress": 0})
        started = datetime.datetime.utcnow()
        try:
            # 1. determine default route and network
            rt = net.get_default_route()
            iface = rt.get("interface")
            gw = rt.get("gateway")
            self._status["iface"] = iface
            self._status["gateway"] = gw
            net_cidr = None
            if iface:
                net_cidr = net.infer_network_from_iface(iface)
            if not net_cidr:
                net_cidr = "192.168.1.0/24"  # fallback conservative
            self._status["network"] = net_cidr
            self._status["progress"] = 10

            # 2. arp/neigh quick pass
            arp_entries = arpmod.read_proc_arp() + arpmod.ip_neigh()
            self._status["progress"] = 25

            # 3. ping_scan via nmap (light)
            hosts = []
            try:
                hosts = nmap_scan.ping_scan(net_cidr)
            except Exception:
                hosts = []
            self._status["progress"] = 55

            ips = [h["ip"] for h in hosts if "ip" in h]
            # 4. services (light) on discovered IPs (batched)
            svc = {}
            if ips:
                try:
                    svc = nmap_scan.service_scan(ips[:30])  # limite para recursos
                except Exception:
                    svc = {}
            self._status["progress"] = 75

            # 5. assemble devices, upsert to DB
            devices = []
            now = datetime.datetime.utcnow().isoformat()
            for h in hosts:
                ip = h.get("ip")
                dev = {
                    "ip": ip,
                    "mac": next((a["mac"] for a in arp_entries if a.get("ip")==ip), ""),
                    "hostname": h.get("hostname", ""),
                    "vendor": "",
                    "device_type": "unknown",
                    "os": "",
                    "last_seen": now,
                    "ports": svc.get(ip, {}).get("ports", [])
                }
                devices.append(dev)
                self.db.upsert_device(dev)
            self._status["progress"] = 90

            # 6. build topology (simple heuristics)
            topology = topo_mod.build_topology(devices, arp_entries, gateway_ip=gw)
            # persist connections
            for e in topology.get("edges", []):
                self.db.insert_connection({
                    "source": e.get("source"),
                    "target": e.get("target"),
                    "confidence": e.get("confidence"),
                    "method": e.get("method"),
                    "detected_at": now
                })
            self._status.update({
                "devices": len(devices),
                "connections": len(topology.get("edges", [])),
                "last_run": now
            })
            self._status["progress"] = 100
        finally:
            self._running = False
            self._status["running"] = False

    def get_devices(self):
        return self.db.list_devices()

    def get_topology(self):
        topo = {"nodes": [], "edges": []}
        # build minimal nodes from devices
        devs = self.get_devices()
        id_map = {}
        for i, d in enumerate(devs, start=1):
            id_map[d["ip"]] = i
            topo["nodes"].append({"id": i, "ip": d["ip"], "hostname": d.get("hostname")})
        conns = self.db.list_topology()
        for c in conns:
            s = id_map.get(c["source_ip"]) or c.get("source_ip")
            t = id_map.get(c["target_ip"]) or c.get("target_ip")
            topo["edges"].append({"source": s, "target": t, "confidence": c["confidence"], "method": c["method"]})
        return topo

    def get_device(self, device_id):
        # Busca por id
        devs = self.get_devices()
        for d in devs:
            if d.get("id") == device_id:
                return d
        return None
