/* Mapeamento de Rede - execução sob demanda, sem persistência */

const TYPE_ICONS = {
    router: '📡',
    switch: '🔀',
    access_point: '📶',
    server: '🖥️',
    desktop: '🖥️',
    notebook: '💻',
    smartphone: '📱',
    printer: '🖨️',
    iot: '🔌',
    network: '🌐',
    unknown: '❓',
};

const btnScan = document.getElementById('btn-scan');
const cidrInput = document.getElementById('network-cidr');
const statusLine = document.getElementById('status-line');
const resultPanel = document.getElementById('result-panel');
const resultSummary = document.getElementById('result-summary');
const warningsBox = document.getElementById('warnings');
const treeContainer = document.getElementById('tree-container');

btnScan.addEventListener('click', runScan);
cidrInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') runScan();
});

async function runScan() {
    const networkCidr = cidrInput.value.trim();

    btnScan.disabled = true;
    btnScan.textContent = '⏳ Mapeando...';
    statusLine.textContent = 'Executando descoberta na rede, isso pode levar alguns instantes...';
    statusLine.className = 'status-line status-running';
    resultPanel.style.display = 'none';
    treeContainer.innerHTML = '';
    warningsBox.innerHTML = '';

    try {
        const response = await fetch('/rede/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ network_cidr: networkCidr }),
        });
        const data = await response.json();

        if (!data.success) {
            statusLine.textContent = '❌ ' + (data.error || 'Falha ao executar o mapeamento.');
            statusLine.className = 'status-line status-error';
            return;
        }

        statusLine.textContent = '';
        statusLine.className = 'status-line';
        renderResult(data);
    } catch (err) {
        statusLine.textContent = '❌ Erro de comunicação com o servidor: ' + err.message;
        statusLine.className = 'status-line status-error';
    } finally {
        btnScan.disabled = false;
        btnScan.textContent = '▶ Executar Mapeamento';
    }
}

function renderResult(data) {
    resultPanel.style.display = 'block';
    resultSummary.textContent = `Rede: ${data.network_cidr} — ${data.device_count} dispositivo(s) encontrado(s)`;

    warningsBox.innerHTML = '';
    (data.warnings || []).forEach((w) => {
        const p = document.createElement('p');
        p.className = 'warning-item';
        p.textContent = '⚠️ ' + w;
        warningsBox.appendChild(p);
    });

    treeContainer.innerHTML = '';
    if (!data.tree) {
        treeContainer.textContent = 'Nenhum dispositivo para exibir.';
        return;
    }

    const rootUl = document.createElement('ul');
    rootUl.className = 'tree-root';
    rootUl.appendChild(renderNode(data.tree));
    treeContainer.appendChild(rootUl);
}

function renderNode(node) {
    const li = document.createElement('li');
    li.className = 'tree-node';

    const icon = TYPE_ICONS[node.type] || TYPE_ICONS.unknown;
    const label = node.hostname && node.hostname !== 'Desconhecido' ? node.hostname : (node.ip || node.hostname);

    const box = document.createElement('div');
    box.className = 'node-box';
    box.innerHTML = `
        <div class="node-title">${icon} ${escapeHtml(label)}</div>
        ${node.ip ? `<div class="node-detail">IP: ${escapeHtml(node.ip)}</div>` : ''}
        ${node.mac ? `<div class="node-detail">MAC: ${escapeHtml(node.mac)}</div>` : ''}
        ${node.vendor && node.vendor !== 'Desconhecido' ? `<div class="node-detail">Fabricante: ${escapeHtml(node.vendor)}</div>` : ''}
        ${node.os && node.os !== 'Desconhecido' ? `<div class="node-detail">SO: ${escapeHtml(node.os)}</div>` : ''}
        ${renderPorts(node.open_ports)}
    `;
    li.appendChild(box);

    if (node.children && node.children.length > 0) {
        const ul = document.createElement('ul');
        node.children.forEach((child) => ul.appendChild(renderNode(child)));
        li.appendChild(ul);
    }

    return li;
}

function renderPorts(ports) {
    if (!ports || ports.length === 0) return '';
    const list = ports.map((p) => `${p.port}/${p.protocol} ${p.service || ''}`.trim()).join(', ');
    return `<div class="node-detail">Portas: ${escapeHtml(list)}</div>`;
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
}
