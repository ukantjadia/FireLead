document.addEventListener('DOMContentLoaded', () => {
    // Initialize charts and load data
    initializeCharts();
    loadDashboardData();
    setupEventListeners();
});

// Initialize all charts
function initializeCharts() {
    // Lead Score Distribution Chart
    const leadScoreCtx = document.getElementById('leadScoreChart').getContext('2d');
    new Chart(leadScoreCtx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Average Lead Score',
                data: [65, 70, 68, 75, 72, 80, 78],
                borderColor: '#2563eb',
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });

    // Lead Quality Distribution Chart
    const qualityDistCtx = document.getElementById('qualityDistChart').getContext('2d');
    new Chart(qualityDistCtx, {
        type: 'doughnut',
        data: {
            labels: ['High Quality', 'Medium', 'Low'],
            datasets: [{
                data: [30, 50, 20],
                backgroundColor: ['#22c55e', '#f59e0b', '#ef4444']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });

    // Industry Distribution Chart
    const industryCtx = document.getElementById('industryChart').getContext('2d');
    new Chart(industryCtx, {
        type: 'bar',
        data: {
            labels: ['Tech', 'Finance', 'Healthcare', 'Retail', 'Others'],
            datasets: [{
                label: 'Companies by Industry',
                data: [45, 30, 25, 20, 15],
                backgroundColor: '#60a5fa'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

// Load dashboard data from the server
async function loadDashboardData() {
    try {
        const response = await fetch('/api/dashboard-data');
        const data = await response.json();
        updateDashboardMetrics(data);
        updateRecentLeadsTable(data.recentLeads);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Update dashboard metrics
function updateDashboardMetrics(data) {
    document.getElementById('totalLeads').textContent = data.totalLeads;
    document.getElementById('avgLeadScore').textContent = data.averageScore;
    
    // Update trend indicators
    const trendValue = document.querySelector('.trend-value');
    const trendIcon = document.querySelector('.trend-icon');
    
    if (data.trend > 0) {
        trendValue.textContent = `+${data.trend}%`;
        trendIcon.textContent = '↑';
        trendIcon.style.color = '#22c55e';
    } else {
        trendValue.textContent = `${data.trend}%`;
        trendIcon.textContent = '↓';
        trendIcon.style.color = '#ef4444';
    }
}

// Update recent leads table
function updateRecentLeadsTable(leads) {
    const tbody = document.querySelector('#recentLeadsTable tbody');
    tbody.innerHTML = '';

    leads.forEach(lead => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${lead.company}</td>
            <td>
                <div class="lead-score ${getScoreClass(lead.score)}">
                    ${lead.score}
                </div>
            </td>
            <td>${lead.industry}</td>
            <td>${lead.contact}</td>
            <td>${formatDate(lead.date)}</td>
            <td>
                <button class="btn-icon" onclick="exportLead('${lead.id}')">
                    <span class="icon">↗</span>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Export functions for different CRM formats
async function exportToCRM(format, data) {
    const exportEndpoints = {
        'hubspot': '/api/export/hubspot',
        'salesforce': '/api/export/salesforce',
        'pipedrive': '/api/export/pipedrive',
        'csv': '/api/export/csv'
    };

    try {
        const response = await fetch(exportEndpoints[format], {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (format === 'csv') {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `leads_export_${formatDate(new Date())}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } else {
            const result = await response.json();
            showNotification(result.message, result.status);
        }
    } catch (error) {
        showNotification('Export failed. Please try again.', 'error');
        console.error('Export error:', error);
    }
}

// Setup event listeners
function setupEventListeners() {
    // Time range filter
    document.getElementById('timeRange').addEventListener('change', (e) => {
        loadDashboardData(e.target.value);
    });

    // Export buttons
    document.querySelectorAll('.export-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const format = btn.dataset.format;
            exportToCRM(format);
        });
    });
}

// Utility functions
function getScoreClass(score) {
    if (score >= 80) return 'high';
    if (score >= 50) return 'medium';
    return 'low';
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}
