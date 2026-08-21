import subprocess
import re
import shlex
from time import time

COMMON_PORTS = "22,23,80,443,161,3306,8080"

def run_cmd(args, timeout=60):
    try:
        out = subprocess.check_output(args, stderr=subprocess.DEVNULL, timeout=timeout)
        return out.decode(errors="ignore")
    except Exception:
        return ""

def ping_scan(cidr):
    # varredura leve: ping scan (-sn)
    args = ["nmap", "-sn", "-n", "-T4", cidr]
    out = run_cmd(args, timeout=60)
    hosts = []
    # parse lines: Nmap scan report for 192.168.3.10
    for line in out.splitlines():
        m = re.match(r"Nmap scan report for\s+([0-9\.]+)(?:\s+\(([^)]+)\))?", line)
        if m:
            ip = m.group(1)
            host = {"ip": ip}
            if m.group(2):
                host["hostname"] = m.group(2)
            hosts.append(host)
    return hosts

def service_scan(ip_list, ports=COMMON_PORTS):
    # varredura de portas para hosts descobertos (leve, apenas portas comuns)
    ips = ",".join(ip_list)
    args = ["nmap", "-sV", "-Pn", "-n", "-T4", "-p", ports, ips]
    out = run_cmd(args, timeout=120)
    results = {}
    # parse simples: "PORT   STATE  SERVICE VERSION" e host lines
    cur_ip = None
    for line in out.splitlines():
        hh = re.match(r"Nmap scan report for\s+([0-9\.]+)", line)
        if hh:
            cur_ip = hh.group(1)
            results[cur_ip] = {"ports": []}
            continue
        p = re.match(r"(\d+)\/tcp\s+(\w+)\s+([\w\-]+)\s*(.*)", line)
        if p and cur_ip:
            port = int(p.group(1))
            state = p.group(2)
            service = p.group(3)
            info = p.group(4).strip()
            results[cur_ip]["ports"].append({"port": port, "state": state, "service": service, "info": info})
    return results
