/* API Utility Functions */

const API_BASE = '/api/network';

// Generic API call function
async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`${API_BASE}${endpoint}`, options);
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Device APIs
async function getDevices() {
    return apiCall('/devices');
}

async function getDevice(ip) {
    return apiCall(`/devices/${ip}`);
}

async function getDevicesByStatus(status) {
    return apiCall(`/devices/status/${status}`);
}

// Connection APIs
async function getConnections() {
    return apiCall('/connections');
}

async function getDeviceConnections(ip) {
    return apiCall(`/connections/${ip}`);
}

// Scan APIs
async function startScan(networkCidr) {
    return apiCall('/scan', 'POST', { network_cidr: networkCidr });
}

async function getScanStatus() {
    return apiCall('/scan/status');
}

async function getScans(limit = 10) {
    return apiCall(`/scans?limit=${limit}`);
}

// Topology APIs
async function getTopology() {
    return apiCall('/topology');
}

async function getNetworkStatus() {
    return apiCall('/network/status');
}

// Config APIs
async function getConfig() {
    return apiCall('/config');
}

async function updateConfig(config) {
    return apiCall('/config', 'POST', config);
}

// Health check
async function healthCheck() {
    return apiCall('/health');
}
