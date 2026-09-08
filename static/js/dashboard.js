/* Dashboard Main Script */

let currentTab = 'dashboard';
let scanInterval = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Inicializando dashboard...');
    
    // Check API health
    try {
        await healthCheck();
        console.log('API conectada');
    } catch (e) {
        console.error('Erro ao conectar com API:', e);
        showAlert('Erro ao conectar com a API', 'error');
        return;
    }
    
    // Setup event listeners
    setupEventListeners();
    
    // Load initial data
    await loadDashboard();
    await loadConfig();
    
    // Refresh data every 30 seconds
    setInterval(loadDashboard, 30000);
});

function setupEventListeners() {
    // Navigation tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            switchTab(tab.dataset.section);
        });
    });
    
    // Scan buttons
    document.getElementById('btn-scan-now').addEventListener('click', triggerScan);
    document.getElementById('btn-scan-stop').addEventListener('click', stopScan);
    
    // Filters
    document.getElementById('search-device').addEventListener('input', filterDevices);
    document.getElementById('filter-type').addEventListener('change', filterDevices);
    document.getElementById('filter-status').addEventListener('change', filterDevices);
    
    // Settings
    document.getElementById('settings-form').addEventListener('submit', saveSettings);
    
    // Modal close
    document.querySelector('.close').addEventListener('click', closeModal);
    document.getElementById('device-modal').addEventListener('click', (e) => {
        if (e.target.id === 'device-modal') closeModal();
    });
}

function switchTab(tabName) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Remove active from all tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(tabName).classList.add('active');
    document.querySelector(`[data-section="${tabName}"]`).classList.add('active');
    
    currentTab = tabName;
    
    // Load specific data for tab
    if (tabName === 'mapa') {
        loadTopologyMap();
    } else if (tabName === 'dispositivos') {
        loadDevices();
    } else if (tabName === 'historico') {
        loadScans();
    }
}

async function loadDashboard() {
    try {
        const status = await getNetworkStatus();
        
        if (status.success && status.status) {
            const s = status.status;
            document.getElementById('total-devices').textContent = s.total_devices || 0;
            document.getElementById('online-devices').textContent = s.online_devices || 0;
            document.getElementById('offline-devices').textContent = s.offline_devices || 0;
            
            // Calculate open ports
            const devices = await getDevices();
            let totalPorts = 0;
            if (devices.success && devices.devices) {
                devices.devices.forEach(d => {
                    totalPorts += (d.open_ports ? d.open_ports.length : 0);
                });
            }
            document.getElementById('open-ports').textContent = totalPorts;
            
            // Load recent activity
            loadRecentActivity();
        }
    } catch (e) {
        console.error('Erro ao carregar dashboard:', e);
    }
}

async function loadRecentActivity() {
    try {
        const scans = await getScans(5);
        const container = document.getElementById('recent-activity');
        container.innerHTML = '';
        
        if (scans.success && scans.scans && scans.scans.length > 0) {
            scans.scans.forEach(scan => {
                const time = new Date(scan.start_time);
                const item = document.createElement('div');
                item.className = 'activity-item';
                item.innerHTML = `
                    <span class="activity-time">${time.toLocaleString('pt-BR')}</span>
                    <div class="activity-text">
                        <strong>Scan da rede ${scan.network_cidr}</strong><br>
                        ${scan.devices_found} dispositivos encontrados (${scan.devices_online} online)
                    </div>
                `;
                container.appendChild(item);
            });
        } else {
            container.innerHTML = '<p class="loading">Nenhuma atividade recente</p>';
        }
    } catch (e) {
        console.error('Erro ao carregar atividade:', e);
    }
}

async function loadDevices() {
    try {
        const result = await getDevices();
        const tbody = document.getElementById('devices-tbody');
        tbody.innerHTML = '';
        
        if (result.success && result.devices) {
            result.devices.forEach(device => {
                const row = document.createElement('tr');
                const statusBadge = `<span class="badge badge-${device.status}">${device.status.toUpperCase()}</span>`;
                const openPorts = device.open_ports ? device.open_ports.length : 0;
                
                row.innerHTML = `
                    <td><code>${device.ip}</code></td>
                    <td>${device.hostname || '-'}</td>
                    <td>${device.mac || '-'}</td>
                    <td>${device.type}</td>
                    <td>${statusBadge}</td>
                    <td>${openPorts}</td>
                    <td><button class="btn-details" onclick="showDeviceDetails('${device.ip}')">Ver Detalhes</button></td>
                `;
                tbody.appendChild(row);
            });
        }
    } catch (e) {
        console.error('Erro ao carregar dispositivos:', e);
        document.getElementById('devices-tbody').innerHTML = '<tr><td colspan="7" class="loading">Erro ao carregar</td></tr>';
    }
}

async function loadScans() {
    try {
        const result = await getScans(20);
        const tbody = document.getElementById('scans-tbody');
        tbody.innerHTML = '';
        
        if (result.success && result.scans) {
            result.scans.forEach(scan => {
                const row = document.createElement('tr');
                const startTime = new Date(scan.start_time);
                const duration = scan.duration_seconds ? `${scan.duration_seconds.toFixed(1)}s` : '-';
                
                row.innerHTML = `
                    <td>${startTime.toLocaleString('pt-BR')}</td>
                    <td>${scan.network_cidr}</td>
                    <td>${scan.devices_found}</td>
                    <td>${scan.devices_online}</td>
                    <td><span class="badge badge-${scan.status}">${scan.status}</span></td>
                    <td>${duration}</td>
                    <td><button class="btn btn-primary" onclick="showScanDetails(${scan.scan_id})">Detalhes</button></td>
                `;
                tbody.appendChild(row);
            });
        }
    } catch (e) {
        console.error('Erro ao carregar scans:', e);
    }
}

function filterDevices() {
    const searchText = document.getElementById('search-device').value.toLowerCase();
    const typeFilter = document.getElementById('filter-type').value;
    const statusFilter = document.getElementById('filter-status').value;
    
    document.querySelectorAll('#devices-tbody tr').forEach(row => {
        const ip = row.cells[0].textContent.toLowerCase();
        const hostname = row.cells[1].textContent.toLowerCase();
        const type = row.cells[3].textContent.toLowerCase();
        const status = row.cells[4].textContent.toLowerCase();
        
        let visible = true;
        
        if (searchText && !ip.includes(searchText) && !hostname.includes(searchText)) {
            visible = false;
        }
        if (typeFilter && !type.includes(typeFilter.toLowerCase())) {
            visible = false;
        }
        if (statusFilter && !status.includes(statusFilter.toLowerCase())) {
            visible = false;
        }
        
        row.style.display = visible ? '' : 'none';
    });
}

async function triggerScan() {
    const cidr = document.getElementById('cidr-input').value;
    if (!cidr) {
        showAlert('Defina o CIDR da rede', 'error');
        return;
    }
    
    document.getElementById('btn-scan-now').disabled = true;
    document.getElementById('scan-progress').style.display = 'block';
    
    try {
        const result = await startScan(cidr);
        if (result.success) {
            showAlert('Scan iniciado com sucesso', 'success');
            monitorScan();
        } else {
            showAlert('Erro ao iniciar scan: ' + result.error, 'error');
        }
    } catch (e) {
        showAlert('Erro ao iniciar scan', 'error');
    }
}

function monitorScan() {
    const checkInterval = setInterval(async () => {
        try {
            const status = await getScanStatus();
            if (status.success && status.status) {
                const s = status.status;
                if (!s.scan_in_progress) {
                    clearInterval(checkInterval);
                    document.getElementById('scan-progress').style.display = 'none';
                    document.getElementById('btn-scan-now').disabled = false;
                    showAlert('Scan concluído', 'success');
                    loadDashboard();
                }
            }
        } catch (e) {
            console.error('Erro ao monitorar scan:', e);
        }
    }, 2000);
}

function stopScan() {
    showAlert('Parar scan não implementado ainda', 'warning');
}

async function loadConfig() {
    try {
        const result = await getConfig();
        if (result.success && result.config) {
            const config = result.config;
            document.getElementById('cidr-input').value = config.network_cidr;
            document.getElementById('interval-input').value = config.scan_interval_seconds;
            document.getElementById('scheduler-toggle').checked = config.scheduler_running;
            document.getElementById('nmap-toggle').checked = config.scanners_enabled.nmap;
            document.getElementById('arp-toggle').checked = config.scanners_enabled.arp;
            document.getElementById('snmp-toggle').checked = config.scanners_enabled.snmp;
        }
    } catch (e) {
        console.error('Erro ao carregar config:', e);
    }
}

async function saveSettings(e) {
    e.preventDefault();
    
    const config = {
        network_cidr: document.getElementById('cidr-input').value,
        scan_interval_seconds: parseInt(document.getElementById('interval-input').value),
        scheduler_running: document.getElementById('scheduler-toggle').checked
    };
    
    try {
        const result = await updateConfig(config);
        if (result.success) {
            showAlert('Configurações salvas', 'success');
        } else {
            showAlert('Erro ao salvar config', 'error');
        }
    } catch (e) {
        showAlert('Erro ao salvar config', 'error');
    }
}

async function showDeviceDetails(ip) {
    try {
        const result = await getDevice(ip);
        if (result.success && result.device) {
            const device = result.device;
            const modal = document.getElementById('device-modal');
            const body = document.getElementById('modal-body');
            
            let portsHtml = '';
            if (result.ports && result.ports.length > 0) {
                portsHtml = '<h3>Portas Abertas</h3><ul>';
                result.ports.forEach(p => {
                    portsHtml += `<li>${p.port}/${p.protocol} - ${p.service} (${p.version})</li>`;
                });
                portsHtml += '</ul>';
            }
            
            body.innerHTML = `
                <h2>${device.hostname || device.ip}</h2>
                <table class="detail-table">
                    <tr><td>IP:</td><td><code>${device.ip}</code></td></tr>
                    <tr><td>MAC:</td><td>${device.mac}</td></tr>
                    <tr><td>Tipo:</td><td>${device.type}</td></tr>
                    <tr><td>Status:</td><td>${device.status}</td></tr>
                    <tr><td>Sistema Operacional:</td><td>${device.os}</td></tr>
                    <tr><td>Modelo:</td><td>${device.model}</td></tr>
                    <tr><td>Fabricante:</td><td>${device.vendor}</td></tr>
                    <tr><td>Primeiro Aparecimento:</td><td>${new Date(device.first_seen).toLocaleString('pt-BR')}</td></tr>
                    <tr><td>Último Aparecimento:</td><td>${new Date(device.last_seen).toLocaleString('pt-BR')}</td></tr>
                </table>
                ${portsHtml}
            `;
            
            modal.classList.add('show');
        }
    } catch (e) {
        showAlert('Erro ao carregar detalhes', 'error');
    }
}

function showScanDetails(scanId) {
    showAlert(`Scan #${scanId}`, 'info');
}

function closeModal() {
    document.getElementById('device-modal').classList.remove('show');
}

function showAlert(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // TODO: Implementar UI toast/alert melhor
}
