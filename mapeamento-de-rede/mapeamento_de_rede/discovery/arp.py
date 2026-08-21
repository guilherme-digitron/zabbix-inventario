import re
import subprocess

def run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=5)
        return out.decode(errors="ignore")
    except Exception:
        return ""

def read_proc_arp():
    # Tenta /proc/net/arp
    try:
        with open("/proc/net/arp") as f:
            lines = f.read().splitlines()[1:]
    except Exception:
        lines = []
    devices = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 6:
            ip = parts[0]
            mac = parts[3]
            device = {"ip": ip, "mac": mac}
            devices.append(device)
    return devices

def ip_neigh():
    out = run_cmd(["ip", "neigh", "show"])
    devices = []
    for line in out.splitlines():
        # ex: 192.168.3.10 dev eth0 lladdr aa:bb:cc:dd:ee:ff REACHABLE
        p = re.match(r"([\d\.]+)\s+dev\s+(\S+)\s+lladdr\s+([0-9a-f:]{17})\s+(\w+)", line, re.I)
        if p:
            devices.append({"ip": p.group(1), "interface": p.group(2), "mac": p.group(3), "state": p.group(4)})
    return devices
