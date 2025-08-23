/**
 * Deckport Admin Panel - Core JavaScript
 * Handles common admin functionality, alerts, modals, and utilities
 */

// Global admin configuration
const AdminConfig = {
    apiBaseUrl: '/admin/api',
    wsUrl: 'ws://127.0.0.1:8003/admin-ws',
    refreshInterval: 30000, // 30 seconds
    alertTimeout: 5000, // 5 seconds
    maxAlerts: 5
};

// Global state
let adminState = {
    isConnected: false,
    websocket: null,
    activeAlerts: [],
    currentUser: null,
    permissions: []
};

/**
 * Initialize admin panel
 */
function initializeAdmin() {
    console.log('🚀 Initializing Deckport Admin Panel');
    
    // Initialize components
    initializeAlerts();
    initializeModals();
    initializeTooltips();
    initializeKeyboardShortcuts();
    
    // Connect to real-time updates
    connectWebSocket();
    
    // Set up periodic health checks
    setInterval(checkSystemHealth, AdminConfig.refreshInterval);
    
    console.log('✅ Admin panel initialized successfully');
}

/**
 * Alert System
 */
function initializeAlerts() {
    // Create alert container if it doesn't exist
    if (!document.getElementById('alert-container')) {
        const container = document.createElement('div');
        container.id = 'alert-container';
        container.className = 'fixed top-4 right-4 z-50 space-y-2';
        document.body.appendChild(container);
    }
}

function showAlert(message, type = 'info', duration = AdminConfig.alertTimeout) {
    const alertId = 'alert-' + Date.now();
    const container = document.getElementById('alert-container');
    
    // Remove oldest alert if we have too many
    if (adminState.activeAlerts.length >= AdminConfig.maxAlerts) {
        const oldestAlert = document.getElementById(adminState.activeAlerts[0]);
        if (oldestAlert) {
            oldestAlert.remove();
        }
        adminState.activeAlerts.shift();
    }
    
    // Create alert element
    const alert = document.createElement('div');
    alert.id = alertId;
    alert.className = `alert alert-${type} fade-in max-w-sm`;
    
    const iconMap = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    alert.innerHTML = `
        <div class="flex items-start space-x-3">
            <div class="flex-shrink-0">
                <i class="${iconMap[type] || iconMap.info}"></i>
            </div>
            <div class="flex-1">
                <p class="text-sm">${message}</p>
            </div>
            <button class="flex-shrink-0 text-gray-400 hover:text-white" onclick="removeAlert('${alertId}')">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    container.appendChild(alert);
    adminState.activeAlerts.push(alertId);
    
    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => removeAlert(alertId), duration);
    }
    
    return alertId;
}

function removeAlert(alertId) {
    const alert = document.getElementById(alertId);
    if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateX(100%)';
        setTimeout(() => {
            alert.remove();
            adminState.activeAlerts = adminState.activeAlerts.filter(id => id !== alertId);
        }, 300);
    }
}

/**
 * Modal System
 */
function initializeModals() {
    // Close modals when clicking outside
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal')) {
            closeModal(event.target.id);
        }
    });
    
    // Close modals with Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const openModal = document.querySelector('.modal:not(.hidden)');
            if (openModal) {
                closeModal(openModal.id);
            }
        }
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
}

/**
 * Tooltip System
 */
function initializeTooltips() {
    // Simple tooltip implementation
    document.querySelectorAll('[data-tooltip]').forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(event) {
    const element = event.target;
    const text = element.getAttribute('data-tooltip');
    
    const tooltip = document.createElement('div');
    tooltip.id = 'tooltip';
    tooltip.className = 'absolute bg-gray-900 text-white text-xs rounded py-1 px-2 z-50';
    tooltip.textContent = text;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
}

function hideTooltip() {
    const tooltip = document.getElementById('tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

/**
 * Keyboard Shortcuts
 */
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
        // Ctrl/Cmd + K: Quick search
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            openQuickSearch();
        }
        
        // Ctrl/Cmd + Shift + D: Toggle dark mode
        if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'D') {
            event.preventDefault();
            toggleDarkMode();
        }
        
        // Ctrl/Cmd + Shift + R: Refresh data
        if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'R') {
            event.preventDefault();
            refreshAllData();
        }
    });
}

/**
 * WebSocket Connection for Real-time Updates
 */
function connectWebSocket() {
    try {
        adminState.websocket = new WebSocket(AdminConfig.wsUrl);
        
        adminState.websocket.onopen = function() {
            console.log('🔌 WebSocket connected');
            adminState.isConnected = true;
            updateConnectionStatus('connected');
        };
        
        adminState.websocket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleRealTimeUpdate(data);
        };
        
        adminState.websocket.onclose = function() {
            console.log('🔌 WebSocket disconnected');
            adminState.isConnected = false;
            updateConnectionStatus('disconnected');
            
            // Attempt to reconnect after 5 seconds
            setTimeout(connectWebSocket, 5000);
        };
        
        adminState.websocket.onerror = function(error) {
            console.error('🔌 WebSocket error:', error);
            updateConnectionStatus('error');
        };
        
    } catch (error) {
        console.error('🔌 WebSocket connection failed:', error);
        updateConnectionStatus('error');
    }
}

function handleRealTimeUpdate(data) {
    switch (data.type) {
        case 'console_status':
            updateConsoleStatus(data.payload);
            break;
        case 'player_count':
            updatePlayerCount(data.payload);
            break;
        case 'match_update':
            updateMatchData(data.payload);
            break;
        case 'system_alert':
            showAlert(data.payload.message, data.payload.type);
            break;
        case 'revenue_update':
            updateRevenueData(data.payload);
            break;
        default:
            console.log('Unknown real-time update:', data);
    }
}

function updateConnectionStatus(status) {
    const indicators = document.querySelectorAll('.real-time-indicator');
    indicators.forEach(indicator => {
        indicator.className = `real-time-indicator ${status}`;
    });
}

/**
 * API Helper Functions
 */
async function apiRequest(endpoint, options = {}) {
    const url = AdminConfig.apiBaseUrl + endpoint;
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    try {
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        showAlert(`API Error: ${error.message}`, 'error');
        throw error;
    }
}

async function apiGet(endpoint) {
    return apiRequest(endpoint, { method: 'GET' });
}

async function apiPost(endpoint, data) {
    return apiRequest(endpoint, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

async function apiPut(endpoint, data) {
    return apiRequest(endpoint, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
}

async function apiDelete(endpoint) {
    return apiRequest(endpoint, { method: 'DELETE' });
}

/**
 * Data Update Functions
 */
function updateConsoleStatus(data) {
    // Update console count displays
    const consoleCountElements = document.querySelectorAll('#console-count, #active-consoles');
    consoleCountElements.forEach(el => {
        if (el) el.textContent = data.active_count;
    });
    
    // Update individual console status in tables
    if (data.console_updates) {
        data.console_updates.forEach(update => {
            const row = document.querySelector(`[data-console-id="${update.console_id}"]`);
            if (row) {
                updateConsoleRow(row, update);
            }
        });
    }
}

function updatePlayerCount(data) {
    const playerCountElements = document.querySelectorAll('#player-count');
    playerCountElements.forEach(el => {
        if (el) el.textContent = data.online_count.toLocaleString();
    });
}

function updateMatchData(data) {
    const matchCountElements = document.querySelectorAll('#match-count, #live-matches');
    matchCountElements.forEach(el => {
        if (el) el.textContent = data.live_matches;
    });
}

function updateRevenueData(data) {
    const revenueElements = document.querySelectorAll('#revenue-count');
    revenueElements.forEach(el => {
        if (el) el.textContent = '$' + data.daily_revenue.toLocaleString();
    });
}

/**
 * System Health Check
 */
async function checkSystemHealth() {
    try {
        const health = await apiGet('/system/health');
        updateSystemHealthDisplay(health);
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

function updateSystemHealthDisplay(health) {
    // Update system health indicators
    Object.entries(health.services).forEach(([service, status]) => {
        const indicator = document.querySelector(`[data-service="${service}"] .status-indicator`);
        if (indicator) {
            indicator.className = `status-indicator ${status.healthy ? 'healthy' : 'unhealthy'}`;
        }
    });
}

/**
 * Utility Functions
 */
function formatNumber(num) {
    return new Intl.NumberFormat().format(num);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDateTime(date) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(date));
}

function formatRelativeTime(date) {
    const now = new Date();
    const diff = now - new Date(date);
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    return 'Just now';
}

/**
 * Loading States
 */
function showLoading(elementId = 'loading-overlay') {
    const overlay = document.getElementById(elementId);
    if (overlay) {
        overlay.classList.remove('hidden');
    }
}

function hideLoading(elementId = 'loading-overlay') {
    const overlay = document.getElementById(elementId);
    if (overlay) {
        overlay.classList.add('hidden');
    }
}

function addLoadingToButton(button) {
    const originalText = button.textContent;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Loading...';
    
    return () => {
        button.disabled = false;
        button.innerHTML = originalText;
    };
}

/**
 * Quick Actions
 */
function openQuickSearch() {
    // Implement quick search functionality
    showAlert('Quick search not implemented yet', 'info');
}

function toggleDarkMode() {
    // Dark mode toggle (already dark, but could implement light mode)
    showAlert('Already in dark mode', 'info');
}

function refreshAllData() {
    showAlert('Refreshing all data...', 'info');
    // Trigger refresh of all dashboard data
    if (window.refreshDashboard) {
        window.refreshDashboard();
    }
}

// Global admin functions
window.broadcastMessage = function() {
    const message = prompt('Enter broadcast message:');
    if (message) {
        if (confirm(`Send message to all active consoles?\n\n"${message}"`)) {
            apiPost('/broadcast', { message })
                .then(() => showAlert('Message broadcasted successfully', 'success'))
                .catch(() => showAlert('Failed to broadcast message', 'error'));
        }
    }
};

window.emergencyStop = function() {
    if (confirm('EMERGENCY STOP: This will immediately halt all console operations. Continue?')) {
        apiPost('/emergency-stop')
            .then(() => showAlert('Emergency stop activated', 'warning'))
            .catch(() => showAlert('Emergency stop failed', 'error'));
    }
};

window.systemBackup = function() {
    if (confirm('Start system backup? This may take several minutes.')) {
        const stopLoading = addLoadingToButton(event.target);
        apiPost('/system/backup')
            .then(() => {
                showAlert('System backup started', 'success');
                stopLoading();
            })
            .catch(() => {
                showAlert('Backup failed to start', 'error');
                stopLoading();
            });
    }
};

window.maintenanceMode = function() {
    const isEnabled = confirm('Enable maintenance mode? This will prevent new player sessions.');
    apiPost('/system/maintenance', { enabled: isEnabled })
        .then(() => showAlert(`Maintenance mode ${isEnabled ? 'enabled' : 'disabled'}`, 'info'))
        .catch(() => showAlert('Failed to toggle maintenance mode', 'error'));
};

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAdmin);
} else {
    initializeAdmin();
}
