/* Topology Visualization */

async function loadTopologyMap() {
    try {
        const result = await getTopology();
        if (result.success) {
            drawTopology(result.nodes, result.edges);
        }
    } catch (e) {
        console.error('Erro ao carregar topologia:', e);
    }
}

function drawTopology(nodes, edges) {
    const svg = document.getElementById('topology-svg');
    svg.innerHTML = ''; // Clear previous content
    
    const width = svg.parentElement.offsetWidth || 1200;
    const height = 600;
    
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    
    // Calculate positions using force-directed layout
    const positions = calculateNodePositions(nodes, edges, width, height);
    
    // Draw edges first
    edges.forEach(edge => {
        const sourcePos = positions[edge.source];
        const targetPos = positions[edge.target];
        
        if (sourcePos && targetPos) {
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', sourcePos.x);
            line.setAttribute('y1', sourcePos.y);
            line.setAttribute('x2', targetPos.x);
            line.setAttribute('y2', targetPos.y);
            line.setAttribute('stroke', edge.confirmed ? '#27AE60' : '#F39C12');
            line.setAttribute('stroke-width', edge.confirmed ? '3' : '2');
            if (!edge.confirmed) {
                line.setAttribute('stroke-dasharray', '5,5');
            }
            line.setAttribute('class', 'edge');
            line.setAttribute('title', `${edge.type} - ${edge.confidence}%`);
            svg.appendChild(line);
        }
    });
    
    // Draw nodes
    const deviceIcons = {
        'router': '🔀',
        'switch': '🔀',
        'access_point': '📶',
        'server': '🖥️',
        'desktop': '💻',
        'notebook': '💻',
        'smartphone': '📱',
        'printer': '🖨️',
        'iot': '🔧',
        'unknown': '❓'
    };
    
    nodes.forEach(node => {
        const pos = positions[node.id];
        if (!pos) return;
        
        // Circle
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', pos.x);
        circle.setAttribute('cy', pos.y);
        circle.setAttribute('r', '25');
        circle.setAttribute('fill', getDeviceColor(node.type));
        circle.setAttribute('stroke', node.status === 'offline' ? '#E74C3C' : '#333');
        circle.setAttribute('stroke-width', node.status === 'offline' ? '3' : '2');
        circle.setAttribute('class', 'node');
        circle.setAttribute('data-ip', node.id);
        circle.addEventListener('click', () => showDeviceDetails(node.id));
        svg.appendChild(circle);
        
        // Label
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', pos.x);
        text.setAttribute('y', pos.y + 40);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('font-size', '11');
        text.setAttribute('fill', '#333');
        text.textContent = node.label.split('.').pop();
        svg.appendChild(text);
    });
}

function calculateNodePositions(nodes, edges, width, height) {
    const positions = {};
    const padding = 50;
    
    // Group nodes by level
    const levels = {};
    nodes.forEach(node => {
        const level = node.level || 0;
        if (!levels[level]) levels[level] = [];
        levels[level].push(node.id);
    });
    
    // Position nodes by level
    Object.keys(levels).sort((a, b) => a - b).forEach((level, idx) => {
        const nodeIds = levels[level];
        const y = padding + (idx * (height - 2 * padding) / Math.max(Object.keys(levels).length - 1, 1));
        const x_step = (width - 2 * padding) / (nodeIds.length + 1);
        
        nodeIds.forEach((nodeId, jdx) => {
            positions[nodeId] = {
                x: padding + x_step * (jdx + 1),
                y: y
            };
        });
    });
    
    return positions;
}

function getDeviceColor(type) {
    const colors = {
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
    };
    return colors[type] || colors['unknown'];
}
