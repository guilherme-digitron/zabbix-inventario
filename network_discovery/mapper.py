"""
Mapeador de Rede — versão sem persistência.

Executa os scanners disponíveis (ARP + Nmap), consolida os dispositivos
encontrados e monta uma árvore simples indicando quem se conecta a quem.
Tudo acontece em memória durante a chamada; nada é salvo em disco.
"""

import ipaddress
import logging
import socket
import concurrent.futures
from typing import Dict, List, Optional

from network_discovery.models import Device, DeviceType
from network_discovery.scanner.arp_scanner import ARPScanner
from network_discovery.scanner.nmap_scanner import NmapScanner
from network_discovery import config

logger = logging.getLogger(__name__)


def get_local_network() -> str:
    """Tenta descobrir a rede local (CIDR /24) para sugerir como padrão"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
        network = ipaddress.IPv4Network(f'{local_ip}/24', strict=False)
        return str(network)
    except Exception:
        return config.DEFAULT_NETWORK_CIDR


def _build_scanners():
    scanners = {}
    if config.ARP_ENABLED:
        arp = ARPScanner()
        if arp.is_available():
            scanners['arp'] = arp
    if config.NMAP_ENABLED:
        nmap = NmapScanner()
        if nmap.is_available():
            scanners['nmap'] = nmap
    return scanners


def _merge(devices: Dict[str, Device], found: List[Device]):
    for device in found:
        if device.ip not in devices:
            devices[device.ip] = device
            continue
        existing = devices[device.ip]
        if device.mac and not existing.mac:
            existing.mac = device.mac
        if device.hostname and not existing.hostname:
            existing.hostname = device.hostname
        if device.os != 'Desconhecido' and existing.os == 'Desconhecido':
            existing.os = device.os
        if device.vendor != 'Desconhecido' and existing.vendor == 'Desconhecido':
            existing.vendor = device.vendor
        if device.device_type != DeviceType.UNKNOWN and existing.device_type == DeviceType.UNKNOWN:
            existing.device_type = device.device_type
        if device.open_ports:
            existing.open_ports = device.open_ports
        for method in device.discovery_methods:
            existing.add_discovery_method(method)


def _identify_gateway(devices: Dict[str, Device], network_cidr: str) -> Optional[str]:
    """Escolhe o dispositivo raiz da árvore (gateway/roteador)"""
    try:
        network = ipaddress.IPv4Network(network_cidr, strict=False)
        candidate_gw = str(network.network_address + 1)
        if candidate_gw in devices:
            return candidate_gw
    except Exception:
        pass

    routers = [ip for ip, d in devices.items() if d.device_type == DeviceType.ROUTER]
    if routers:
        return routers[0]

    ones = [ip for ip in devices if ip.endswith('.1')]
    if ones:
        return ones[0]

    return None


def _build_tree(devices: Dict[str, Device], network_cidr: str) -> dict:
    """Monta a árvore: raiz = gateway; demais dispositivos como filhos.

    Dispositivos do tipo access_point/switch aparecem como nós
    intermediários e "roubam" os clientes móveis/IoT como seus filhos,
    já que normalmente é por eles que esses dispositivos se conectam.
    """
    gateway_ip = _identify_gateway(devices, network_cidr)

    def node_for(ip: str) -> dict:
        d = devices[ip]
        node = d.to_dict()
        node['children'] = []
        return node

    if gateway_ip is None:
        root = {
            'ip': None,
            'hostname': network_cidr,
            'mac': None,
            'type': 'network',
            'os': None,
            'vendor': None,
            'open_ports': [],
            'discovery_methods': [],
            'children': [node_for(ip) for ip in devices],
        }
        return root

    root = node_for(gateway_ip)
    remaining = {ip: d for ip, d in devices.items() if ip != gateway_ip}

    intermediaries = {
        ip: node_for(ip) for ip, d in remaining.items()
        if d.device_type in (DeviceType.SWITCH, DeviceType.ACCESS_POINT)
    }
    mobile_types = (DeviceType.SMARTPHONE, DeviceType.IOT, DeviceType.NOTEBOOK)

    leftover_children = []
    inter_ips = list(intermediaries.keys())

    for ip, d in remaining.items():
        if ip in intermediaries:
            continue
        if inter_ips and d.device_type in mobile_types:
            # Anexa a um nó intermediário (round-robin simples)
            target_ip = inter_ips[hash(ip) % len(inter_ips)]
            intermediaries[target_ip]['children'].append(node_for(ip))
        else:
            leftover_children.append(node_for(ip))

    root['children'] = list(intermediaries.values()) + leftover_children
    return root


def _count_nodes(node: dict) -> int:
    return 1 + sum(_count_nodes(c) for c in node.get('children', []))


def run_mapping(network_cidr: str) -> dict:
    """Executa o mapeamento completo e devolve o resultado pronto para a UI"""
    network_cidr = (network_cidr or '').strip() or config.DEFAULT_NETWORK_CIDR

    try:
        ipaddress.IPv4Network(network_cidr, strict=False)
    except ValueError:
        return {'success': False, 'error': f'CIDR inválido: {network_cidr}'}

    scanners = _build_scanners()
    if not scanners:
        return {
            'success': False,
            'error': 'Nenhum scanner disponível neste sistema (nmap/arp não encontrados).',
        }

    devices: Dict[str, Device] = {}
    warnings = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(scanners)) as executor:
        futures = {executor.submit(s.scan, network_cidr): name for name, s in scanners.items()}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                found = future.result()
                _merge(devices, found)
                logger.info(f'{name}: {len(found)} dispositivos')
            except Exception as e:
                warnings.append(f'Falha no scanner {name}: {e}')
                logger.error(f'Erro no scanner {name}: {e}')

    if 'nmap' not in scanners:
        warnings.append('Nmap não disponível: apenas dispositivos na tabela ARP local foram detectados, sem portas/SO.')

    if not devices:
        return {
            'success': True,
            'network_cidr': network_cidr,
            'device_count': 0,
            'tree': None,
            'warnings': warnings + ['Nenhum dispositivo encontrado.'],
        }

    tree = _build_tree(devices, network_cidr)

    return {
        'success': True,
        'network_cidr': network_cidr,
        'device_count': len(devices),
        'tree': tree,
        'warnings': warnings,
    }
