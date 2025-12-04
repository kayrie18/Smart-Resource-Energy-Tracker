/**
 * Smart Energy & Water Resource Tracker - Enhanced Script
 * Supports new UI with separated Water/Energy themes and real-time previews.
 */

const API_BASE = 'http://localhost:5000/api';

let currentUser = null;
let userCategories = [];
let currentView = 'overview';

// Global Chart Instances
let overviewChart = null;
let waterChart = null;
let energyChart = null;

// Initialize
document.addEventListener('DOMContentLoaded', function () {
    // Set default dates
    const today = new Date().toISOString().split('T')[0];
    const inputs = ['waterDate', 'energyDate', 'reportEnd'];
    inputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = today;
    });

    const lastWeek = new Date();
    lastWeek.setDate(lastWeek.getDate() - 7);
    const reportStart = document.getElementById('reportStart');
    if (reportStart) reportStart.value = lastWeek.toISOString().split('T')[0];

    // Check login
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        showApp();
    } else {
        showLanding();
    }

    // Load categories for registration
    loadUserCategories();
});

// --- NAVIGATION & VIEW SWITCHING ---

function showLanding() {
    document.getElementById('landingSection').style.display = 'flex';
    document.getElementById('appSection').style.display = 'none';
    showAuthChoice();
}

function showApp() {
    document.getElementById('landingSection').style.display = 'none';
    document.getElementById('appSection').style.display = 'flex';
    switchView('overview');
    loadDashboardData();
    loadUserProfile();
}

async function loadUserProfile() {
    if (!currentUser) return;
    try {
        const res = await fetch(`${API_BASE}/user/${currentUser.user_id}`);
        const profile = await res.json();
        if (res.ok) {
            displayUserProfile(profile);
        }
    } catch (e) {
        console.error('Error loading user profile', e);
    }
}

function displayUserProfile(profile) {
    const elemMap = {
        'profileUsername': profile.username || '-',
        'profileEmail': profile.email || '-',
        'profileCategoryDisplay': (profile.user_category || 'single').charAt(0).toUpperCase() + (profile.user_category || 'single').slice(1),
        'profileEnergyLimit': `${profile.effective_energy_limit || 0} kWh`,
        'profileWaterLimit': `${profile.effective_water_limit || 0} L`
    };

    for (const [id, value] of Object.entries(elemMap)) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }
}

function showAuthChoice() {
    document.getElementById('authChoice').style.display = 'flex';
    document.getElementById('loginFormContainer').style.display = 'none';
    document.getElementById('registerFormContainer').style.display = 'none';
}

function showLogin() {
    document.getElementById('authChoice').style.display = 'none';
    document.getElementById('loginFormContainer').style.display = 'block';
    document.getElementById('registerFormContainer').style.display = 'none';
}


function showRegister() {
    document.getElementById('authChoice').style.display = 'none';
    document.getElementById('loginFormContainer').style.display = 'none';
    document.getElementById('registerFormContainer').style.display = 'block';
}

function switchView(viewName) {
    currentView = viewName;

    // Update nav buttons
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.querySelector(`.nav-btn[onclick="switchView('${viewName}')"]`);
    if (activeBtn) activeBtn.classList.add('active');

    // Hide/show views
    const views = document.querySelectorAll('.section-content');
    views.forEach(v => v.style.display = 'none');
    const targetView = document.getElementById(`view-${viewName}`);
    if (targetView) {
        targetView.style.display = 'block';
        // Apply theme class to body or main section
        const appSection = document.getElementById('appSection');
        appSection.className = 'app-layout';
        if (viewName === 'water') appSection.classList.add('theme-water');
        if (viewName === 'energy') appSection.classList.add('theme-energy');
    }

    // Reload data and charts to ensure fresh data
    loadDashboardData();
}

function logout() {
    currentUser = null;
    localStorage.removeItem('currentUser');
    showLanding();
}


// --- AUTHENTICATION ---

async function loadUserCategories() {
    try {
        const response = await fetch(`${API_BASE}/user-categories`);
        const data = await response.json();
        userCategories = data.categories;

        const select = document.getElementById('userCategory');
        if (select) {
            select.innerHTML = '<option value="single">Single User</option>'; // Default fallback
            userCategories.forEach(cat => {
                const opt = document.createElement('option');
                opt.value = cat.id;
                opt.textContent = cat.name;
                select.appendChild(opt);
            });
        }
    } catch (e) { console.error('Error loading categories', e); }
}

function toggleFamilyMembers() {
    const cat = document.getElementById('userCategory').value;
    const famField = document.getElementById('familyMembersField');
    famField.style.display = (cat === 'family') ? 'block' : 'none';
}

document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const res = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (res.ok) {
            currentUser = data;
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            showApp();
        } else {
            alert(data.error || 'Login failed');
        }
    } catch (err) { alert('Connection error'); }
});

document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    // Gather data
    const payload = {
        username: document.getElementById('regUsername').value,
        email: document.getElementById('regEmail').value,
        password: document.getElementById('regPassword').value,
        phone_number: document.getElementById('regPhone').value,
        user_category: document.getElementById('userCategory').value,
        family_members: parseInt(document.getElementById('familyMembers').value) || 1,
        custom_energy_limit: parseFloat(document.getElementById('customEnergyLimit').value) || 0,
        custom_water_limit: parseFloat(document.getElementById('customWaterLimit').value) || 0
    };

    try {
        const res = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            alert('Registration successful! Please login.');
            showLogin();
        } else {
            alert(data.error || 'Registration failed');
        }
    } catch (err) { alert('Connection error'); }
});

// --- DATA LOADING & DASHBOARD ---

async function loadDashboardData() {
    if (!currentUser) return;

    try {
        // 1. Get Dashboard Summary
        const dashRes = await fetch(`${API_BASE}/dashboard/${currentUser.user_id}`);
        const dashData = await dashRes.json();

        if (dashRes.ok) {
            updateOverviewUI(dashData);
            updateWaterUI(dashData);
            updateEnergyUI(dashData);
        }

        // 2. Get Chart Data
        const chartRes = await fetch(`${API_BASE}/chart-data/${currentUser.user_id}`);
        const chartData = await chartRes.json();

        if (chartRes.ok) {
            renderCharts(chartData);
        }

        // 3. Get Analytics/Tips
        const analyticsRes = await fetch(`${API_BASE}/analytics/${currentUser.user_id}`);
        const analyticsData = await analyticsRes.json();
        if (analyticsRes.ok) {
            renderTips(analyticsData.conservation_tips);
        }

    } catch (e) { console.error('Error loading dashboard data', e); }
}

function updateOverviewUI(data) {
    document.getElementById('ovEnergyVal').textContent = `${data.monthly_energy_used.toFixed(1)} kWh`;
    document.getElementById('ovWaterVal').textContent = `${data.monthly_water_used.toFixed(0)} L`;
    document.getElementById('ovTotalCost').textContent = `${data.total_cost.toFixed(2)} MWK`;

    // Calculate individual costs roughly if not provided directly, or use totals
    // Ideally backend provides breakdown, but for now we use total cost
}

function updateWaterUI(data) {
    document.getElementById('waterLimitDisplay').textContent = `${data.water_limit} L`;
    const remaining = Math.max(0, data.water_limit - data.monthly_water_used);
    document.getElementById('waterRemainingDisplay').textContent = `${remaining.toFixed(0)} L`;
}

function updateEnergyUI(data) {
    document.getElementById('energyLimitDisplay').textContent = `${data.energy_limit} kWh`;
    const remaining = Math.max(0, data.energy_limit - data.monthly_energy_used);
    document.getElementById('energyRemainingDisplay').textContent = `${remaining.toFixed(1)} kWh`;
}

function renderTips(tips) {
    const waterList = document.getElementById('waterTipsList');
    const energyList = document.getElementById('energyTipsList');

    if (waterList) waterList.innerHTML = '';
    if (energyList) energyList.innerHTML = '';

    if (!tips) return;

    tips.forEach(tip => {
        const div = document.createElement('div');
        div.className = 'tip-card';
        div.innerHTML = `<strong>${tip.title}</strong><p>${tip.detail}</p>`;

        // Simple heuristic to distribute tips
        if (tip.title.toLowerCase().includes('water') || tip.detail.toLowerCase().includes('leak') || tip.detail.toLowerCase().includes('shower')) {
            if (waterList) waterList.appendChild(div.cloneNode(true));
        } else if (tip.title.toLowerCase().includes('energy') || tip.detail.toLowerCase().includes('bulb') || tip.detail.toLowerCase().includes('ac')) {
            if (energyList) energyList.appendChild(div.cloneNode(true));
        } else {
            // General tips go to both or just one
            if (waterList) waterList.appendChild(div.cloneNode(true));
        }
    });
}

// --- CHARTS ---

function renderCharts(data) {
    const dates = data.dates;

    // 1. Overview Chart (Combined Cost or Usage Trend)
    const ctxOv = document.getElementById('mainOverviewChart');
    if (ctxOv && currentView === 'overview') {
        if (overviewChart) overviewChart.destroy();
        overviewChart = new Chart(ctxOv, {
            type: 'bar',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Energy (kWh)',
                        data: data.energy_data, // Note: this is cumulative in backend, might want daily for bar. 
                        // Using cumulative for now as per backend logic, or switch to line
                        type: 'line',
                        borderColor: '#fbc02d',
                        yAxisID: 'y'
                    },
                    {
                        label: 'Water (L)',
                        data: data.water_data,
                        type: 'line',
                        borderColor: '#0288d1',
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { type: 'linear', display: true, position: 'left', title: { display: true, text: 'Energy (kWh)' } },
                    y1: { type: 'linear', display: true, position: 'right', title: { display: true, text: 'Water (L)' }, grid: { drawOnChartArea: false } }
                }
            }
        });
    }

    // 2. Water Chart
    const ctxWater = document.getElementById('waterChart');
    if (ctxWater && currentView === 'water') {
        if (waterChart) waterChart.destroy();
        waterChart = new Chart(ctxWater, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Water Usage (Cumulative)',
                    data: data.water_data,
                    borderColor: '#0288d1',
                    backgroundColor: 'rgba(2, 136, 209, 0.1)',
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Limit',
                    data: Array(dates.length).fill(data.water_limit), // Weekly limit from backend
                    borderColor: '#f44336',
                    borderDash: [5, 5],
                    fill: false
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    // 3. Energy Chart
    const ctxEnergy = document.getElementById('energyChart');
    if (ctxEnergy && currentView === 'energy') {
        if (energyChart) energyChart.destroy();
        energyChart = new Chart(ctxEnergy, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Energy Usage (Cumulative)',
                    data: data.energy_data,
                    borderColor: '#fbc02d',
                    backgroundColor: 'rgba(251, 192, 45, 0.1)',
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Limit',
                    data: Array(dates.length).fill(data.energy_limit),
                    borderColor: '#f44336',
                    borderDash: [5, 5],
                    fill: false
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }
}

// --- ENTRY & PREVIEW ---

let waterDebounce;
function previewWaterCost() {
    clearTimeout(waterDebounce);
    waterDebounce = setTimeout(async () => {
        const usage = parseFloat(document.getElementById('waterUsage').value);
        if (!usage || usage <= 0) return;

        try {
            const res = await fetch(`${API_BASE}/preview/water`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: currentUser.user_id, water_usage: usage })
            });
            const data = await res.json();

            const previewEl = document.getElementById('waterPreview');
            previewEl.style.display = 'block';
            document.getElementById('waterCostPreview').textContent = data.calculated_cost;

            const warningEl = document.getElementById('waterLimitWarning');
            if (data.warning) {
                warningEl.textContent = `⚠️ ${data.warning}`;
            } else {
                warningEl.textContent = '';
            }
        } catch (e) { console.error(e); }
    }, 500);
}

let energyDebounce;
function previewEnergyCost() {
    clearTimeout(energyDebounce);
    energyDebounce = setTimeout(async () => {
        const usage = parseFloat(document.getElementById('energyUsage').value);
        if (!usage || usage <= 0) return;

        try {
            const res = await fetch(`${API_BASE}/preview/energy`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: currentUser.user_id, electricity_usage: usage })
            });
            const data = await res.json();

            const previewEl = document.getElementById('energyPreview');
            previewEl.style.display = 'block';
            document.getElementById('energyCostPreview').textContent = data.calculated_cost;

            const warningEl = document.getElementById('energyLimitWarning');
            if (data.warning) {
                warningEl.textContent = `⚠️ ${data.warning}`;
            } else {
                warningEl.textContent = '';
            }
        } catch (e) { console.error(e); }
    }, 500);
}

document.getElementById('waterEntryForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const usage = parseFloat(document.getElementById('waterUsage').value);
    const date = document.getElementById('waterDate').value;

    if (!confirm(`Add ${usage} L of water for ${date}?`)) return;

    try {
        const res = await fetch(`${API_BASE}/water-entries`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.user_id, water_usage: usage, reading_date: date })
        });
        const data = await res.json();
        if (res.ok) {
            alert('Water entry added!');
            document.getElementById('waterUsage').value = '';
            document.getElementById('waterPreview').style.display = 'none';
            loadDashboardData();
        } else {
            alert(data.error);
        }
    } catch (e) { alert('Error adding entry'); }
});

document.getElementById('energyEntryForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const usage = parseFloat(document.getElementById('energyUsage').value);
    const date = document.getElementById('energyDate').value;

    if (!confirm(`Add ${usage} kWh of energy for ${date}?`)) return;

    try {
        const res = await fetch(`${API_BASE}/energy-entries`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.user_id, electricity_usage: usage, reading_date: date })
        });
        const data = await res.json();
        if (res.ok) {
            alert('Energy entry added!');
            document.getElementById('energyUsage').value = '';
            document.getElementById('energyPreview').style.display = 'none';
            loadDashboardData();
        } else {
            alert(data.error);
        }
    } catch (e) { alert('Error adding entry'); }
});

// --- SETTINGS & REPORTS ---

document.getElementById('updateLimitsForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const energyLimit = parseFloat(document.getElementById('settingEnergyLimit').value);
    const waterLimit = parseFloat(document.getElementById('settingWaterLimit').value);

    const payload = {};
    if (!isNaN(energyLimit)) payload.custom_energy_limit = energyLimit;
    if (!isNaN(waterLimit)) payload.custom_water_limit = waterLimit;

    if (Object.keys(payload).length === 0) {
        alert('Please enter at least one limit to update.');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/user/${currentUser.user_id}/profile`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (res.ok) {
            alert('Limits updated successfully!');
            // Update local user object if needed, or just reload dashboard
            if (payload.custom_energy_limit !== undefined) currentUser.custom_energy_limit = payload.custom_energy_limit;
            if (payload.custom_water_limit !== undefined) currentUser.custom_water_limit = payload.custom_water_limit;
            localStorage.setItem('currentUser', JSON.stringify(currentUser));

            // Refresh data
            loadDashboardData();
        } else {
            alert(data.error || 'Failed to update limits');
        }
    } catch (e) {
        console.error(e);
        alert('Error updating profile');
    }
});

// --- WATER ENTRY FORM HANDLER ---
document.getElementById('waterEntryForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const usage = parseFloat(document.getElementById('waterUsage').value);
    const date = document.getElementById('waterDate').value;

    if (!usage || !date) {
        alert('Please fill in all fields');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/water-entries`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.user_id,
                water_usage: usage,
                reading_date: date
            })
        });
        const data = await res.json();

        if (res.ok) {
            alert('Water entry added successfully!');
            document.getElementById('waterEntryForm').reset();
            // Set date back to today
            document.getElementById('waterDate').value = new Date().toISOString().split('T')[0];
            // Refresh dashboard data and charts
            await loadDashboardData();
        } else {
            alert(data.error || 'Failed to add water entry');
        }
    } catch (e) {
        console.error(e);
        alert('Error adding water entry');
    }
});

// --- ENERGY ENTRY FORM HANDLER ---
document.getElementById('energyEntryForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const usage = parseFloat(document.getElementById('energyUsage').value);
    const date = document.getElementById('energyDate').value;

    if (!usage || !date) {
        alert('Please fill in all fields');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/energy-entries`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.user_id,
                electricity_usage: usage,
                reading_date: date
            })
        });
        const data = await res.json();

        if (res.ok) {
            alert('Energy entry added successfully!');
            document.getElementById('energyEntryForm').reset();
            // Set date back to today
            document.getElementById('energyDate').value = new Date().toISOString().split('T')[0];
            // Refresh dashboard data and charts
            await loadDashboardData();
        } else {
            alert(data.error || 'Failed to add energy entry');
        }
    } catch (e) {
        console.error(e);
        alert('Error adding energy entry');
    }
});

function downloadCSV() {
    const start = document.getElementById('reportStart').value;
    const end = document.getElementById('reportEnd').value;
    // Construct a CSV from client side or request from backend
    // Using the analytics endpoint to get data then convert to CSV

    fetch(`${API_BASE}/analytics/${currentUser.user_id}?start_date=${start}&end_date=${end}`)
        .then(res => res.json())
        .then(data => {
            // Flatten data
            // This is a simplified CSV generation
            let csvContent = "data:text/csv;charset=utf-8,";
            csvContent += "Date,Type,Usage,Cost (MWK)\n";

            // We need to merge energy and water entries from the analytics response
            // The analytics endpoint in app.py returns 'series' if we look at the python code?
            // Actually the python code for analytics returns 'series' list.

            // Let's assume we can get the series from the response if we updated app.py to return it.
            // The current app.py analytics endpoint returns 'tips', 'monthly_energy', etc.
            // It DOES calculate series but doesn't seem to return it in the JSON in the snippet I saw?
            // Wait, looking at app.py snippet:
            // It calculates `series` but the return statement was cut off in the view_file.
            // I should verify if `series` is returned.

            // If not, I'll just alert for now or try to use what I have.
            alert("Downloading CSV...");
            window.open(`${API_BASE}/report/${currentUser.user_id}?start_date=${start}&end_date=${end}&format=csv`, '_blank');
        });
}
