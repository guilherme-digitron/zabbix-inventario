import subprocess
import ipaddress
import re

def run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, shell=False, stderr=subprocess.DEVNULL, timeout=5)
        return out.decode(errors="ignore")
    except Exception:
        return ""

def get_default_route():
    # usa `ip route` para descobrir gateway e interface
    out = run_cmd(["ip", "route", "show", "default"])
    # Exemplo: "default via 192.168.3.1 dev eth0 proto dhcp ..."
    m = re.search(r"default via ([0-9.:\w]+) dev (\w+)", out)
    if m:
        return {"gateway": m.group(1), "interface": m.group(2)}
    return {}

def get_interface_cidr(iface):
    out = run_cmd(["ip", "-4", "addr", "show", "dev", iface])
    # procura "inet 192.168.3.141/24"
    m = re.search(r"inet\s+([0-9.]+/\d+)", out)
    if m:
        return m.group(1)
    return None

def infer_network_from_iface(iface):
    cidr = get_interface_cidr(iface)
    if not cidr:
        return None
    net = ipaddress.ip_network(cidr, strict=False)
    return str(net)
