"""
Geral de Gráficos (SVG)
"""

import logging
import math
from typing import List, Dict
from network_discovery.database.models import Device


class GraphGenerator:
    """Gera representação visual (SVG) da topologia"""
    
    def __init__(self, width: int = 1200, height: int = 800):
        self.width = width
        self.height = height
        self.logger = logging.getLogger(__name__)
        self.device_colors = {
            'router': '#FF6B6B',
            'switch': '#4ECDC4',
            'access_point': '#45B7D1',
            'server': '#F7B731',
            'desktop': '#5F27CD',
            'notebook': '#00D2D3',
            'smartphone': '#FF9FF3',
            'printer': '#54A0FF',
            'iot': '#48DBFB',
            'unknown': '#95A5A6'
        }
        self.device_icons = {
            'router': '🔀',
            'switch': '🔌',
            'access_point': '📶',
            'server': '🖥️',
            'desktop': '💻',
            'notebook': '💼',
            'smartphone': '📱',
            'printer': '🖨️',
            'iot': '🔧',
            'unknown': '❓'
        }

    def generate_svg(self, topology_data: Dict) -> str:
        """Gera SVG da topologia"""
        self.logger.info('Gerando SVG da topologia')
        
        nodes = topology_data.get('nodes', [])
        edges = topology_data.get('edges', [])
        
        # Calcular posições dos nós
        positions = self._calculate_positions(nodes, edges)
        
        # Gerar SVG
        svg_parts = []
        svg_parts.append(self._get_svg_header())
        
        # Desenhar conexões (primeiro, para ficar atrás)
        for edge in edges:
            svg_parts.append(self._draw_edge(edge, positions))
        
        # Desenhar nós
        for node in nodes:
            svg_parts.append(self._draw_node(node, positions))
        
        svg_parts.append(self._get_svg_footer())
        
        return '\n'.join(svg_parts)

    def _get_svg_header(self) -> str:
        """Retorna header do SVG"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}">
  <defs>
    <style>
      .node {{ cursor: pointer; }}
      .node:hover circle {{ stroke-width: 3; }}
      .node text {{ font-family: Arial, sans-serif; font-size: 12px; text-anchor: middle; pointer-events: none; }}
      .edge {{ stroke: #999; stroke-width: 2; }}
      .edge.confirmed {{ stroke: #27AE60; stroke-width: 3; }}
      .edge.inferred {{ stroke: #F39C12; stroke-dasharray: 5,5; }}
      .label {{ font-family: Arial, sans-serif; font-size: 11px; }}
    </style>
  </defs>
  <rect width="{self.width}" height="{self.height}" fill="#F5F5F5"/>
  <!-- Rede TCP/IP - Mapa de Topologia -->'''

    def _get_svg_footer(self) -> str:
        """Retorna footer do SVG"""
        return '''\n</svg>'''

    def _calculate_positions(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, tuple]:
        """Calcula posições dos nós usando força-direção"""
        if not nodes:
            return {}
        
        # Usar nível de topologia se disponível
        positions = {}
        levels = defaultdict(list)
        
        for node in nodes:
            level = node.get('level', 0)
            levels[level].append(node['id'])
        
        # Distribuir nós por nível
        max_level = max(levels.keys()) if levels else 0
        
        for level, node_ids in levels.items():
            y = (self.height // (max_level + 2)) * (level + 1)
            x_step = self.width / (len(node_ids) + 1)
            
            for idx, node_id in enumerate(node_ids):
                x = x_step * (idx + 1)
                positions[node_id] = (x, y)
        
        return positions

    def _draw_node(self, node: Dict, positions: Dict) -> str:
        """Desenha um nó (dispositivo)"""
        node_id = node['id']
        if node_id not in positions:
            return ''
        
        x, y = positions[node_id]
        device_type = node.get('type', 'unknown')
        status = node.get('status', 'unknown')
        label = node.get('label', node_id)
        
        color = self.device_colors.get(device_type, self.device_colors['unknown'])
        icon = self.device_icons.get(device_type, self.device_icons['unknown'])
        
        # Adicionar borda vermelha se offline
        stroke_color = '#E74C3C' if status == 'offline' else '#333'
        stroke_width = '3' if status == 'offline' else '2'
        
        svg = f'''  <g class="node" id="node_{node_id}" data-ip="{node_id}">
    <circle cx="{x}" cy="{y}" r="30" fill="{color}" stroke="{stroke_color}" stroke-width="{stroke_width}" />
    <text x="{x}" y="{y + 35}" class="label">{label}</text>
  </g>'''
        
        return svg

    def _draw_edge(self, edge: Dict, positions: Dict) -> str:
        """Desenha uma aresta (conexão)"""
        source = edge.get('source')
        target = edge.get('target')
        
        if source not in positions or target not in positions:
            return ''
        
        x1, y1 = positions[source]
        x2, y2 = positions[target]
        
        connection_type = edge.get('type', 'unknown')
        confirmed = edge.get('confirmed', False)
        confidence = edge.get('confidence', 0)
        
        # Classe CSS para estilo
        css_class = 'edge confirmed' if confirmed else 'edge inferred'
        
        # Tooltip com informações
        title = f'{connection_type.upper()} - Confiabilidade: {confidence}%'
        
        svg = f'''  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{css_class}">
    <title>{title}</title>
  </line>'''
        
        return svg


from collections import defaultdict
