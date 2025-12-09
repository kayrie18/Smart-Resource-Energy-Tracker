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

    // Check login - Auto-login disabled per user request
    /*
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        showApp();
    } else {
        showLanding();
    }
    */
    showLanding(); // Always show landing first


    // Load categories for registration
    loadUserCategories();

    // Register Service Worker for PWA
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('./sw.js')
            .then(() => console.log('Service Worker Registered'))
            .catch(err => console.error('Service Worker Failed', err));
    }

    // Initialize Theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
});

// --- THEME & UI ---

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const newTheme = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const btn = document.getElementById('themeToggle');
    if (btn) btn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
}

// toggleTheme removed as per user request for original interface

function showToast(message, type = 'success') {
    // Revert to alert for errors/warnings, simplified for success
    if (type === 'error' || type === 'warning') {
        alert(message);
    } else {
        // Optional: console.log or simple alert for success
        console.log(message);
    }
}

// --- NAVIGATION & VIEW SWITCHING ---

function showLanding() {
    document.getElementById('landingSection').style.display = 'flex';
    document.getElementById('appSection').style.display = 'none';
    showAuthChoice();
}

function showApp() {
    document.getElementById('landingSection').style.display = 'none';
    document.getElementById('appSection').style.display = 'flex';

    // Show Admin Button if admin
    const adminBtn = document.getElementById('nav-admin');
    if (adminBtn && currentUser) {
        // Ensure strictly boolean check or truthy
        adminBtn.style.display = currentUser.is_admin ? 'block' : 'none';
        console.log("Admin check:", currentUser.is_admin);
    }

    switchView('overview');
    loadDashboardData();
    loadUserProfile();
    loadAchievements();
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

function logout() {
    localStorage.removeItem('currentUser');
    currentUser = null;
    showLanding();
    // Clear forms
    document.getElementById('loginForm').reset();
    document.getElementById('registerForm').reset();
    showToast('Logged out successfully');
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
    showToast('Logged out successfully', 'success');
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
    console.log("Login form submitted");
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const res = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        console.log("Login response:", res.status, data);

        if (res.ok) {
            currentUser = data;
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            console.log("Calling showApp()...");
            showApp();
            showToast(`Welcome back, ${currentUser.username}!`);
        } else {
            console.error("Login failed:", data.error);
            showToast(data.error || 'Login failed', 'error');
        }
    } catch (err) {
        console.error("Login exception:", err);
        showToast('Connection error', 'error');
    }
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
            showToast('Registration successful! Please login.', 'success');
            showLogin();
        } else {
            showToast(data.error || 'Registration failed', 'error');
        }
    } catch (err) { showToast('Connection error', 'error'); }
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
    document.getElementById('ovEnergyVal').textContent = `${data.monthly_energy_used.toFixed(1)} kWh/mo`;
    document.getElementById('ovWaterVal').textContent = `${data.monthly_water_used.toFixed(0)} L/mo`;
    document.getElementById('ovTotalCost').textContent = `${data.total_cost.toFixed(2)} MWK`;

    // Render Trends Chart
    renderUsageTrendsChart(
        data.weekly_energy_used,
        data.prev_weekly_energy_used || 0,
        data.weekly_water_used,
        data.prev_weekly_water_used || 0
    );
}

let trendsChart = null;

function renderUsageTrendsChart(currEnergy, prevEnergy, currWater, prevWater) {
    const ctx = document.getElementById('usageTrendsChart');
    if (!ctx) return;

    if (trendsChart) {
        trendsChart.destroy();
    }

    trendsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Energy (kWh)', 'Water (L/100)'], // Scaled water for visibility
            datasets: [
                {
                    label: 'This Week',
                    data: [currEnergy, currWater / 100],
                    backgroundColor: ['rgba(251, 192, 45, 0.7)', 'rgba(2, 136, 209, 0.7)'],
                    borderColor: ['rgba(251, 192, 45, 1)', 'rgba(2, 136, 209, 1)'],
                    borderWidth: 1
                },
                {
                    label: 'Last Week',
                    data: [prevEnergy, prevWater / 100],
                    backgroundColor: ['rgba(224, 224, 224, 0.7)', 'rgba(224, 224, 224, 0.7)'],
                    borderColor: ['#9e9e9e', '#9e9e9e'],
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Usage Units' }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            let val = context.raw;
                            // Unscale water for tooltip
                            if (context.label.includes('Water')) {
                                val = val * 100;
                                return label + val.toFixed(0) + ' L';
                            }
                            return label + val.toFixed(1) + ' kWh';
                        }
                    }
                }
            }
        }
    });
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
    const dashboardAlerts = document.getElementById('dashboardAlerts');

    if (waterList) waterList.innerHTML = '';
    if (energyList) energyList.innerHTML = '';
    if (dashboardAlerts) dashboardAlerts.innerHTML = '';

    if (!tips || tips.length === 0) {
        if (dashboardAlerts) dashboardAlerts.innerHTML = '<p style="color:#888; font-style:italic;">No recent alerts.</p>';
        return;
    }

    let hasAlerts = false;

    tips.forEach(tip => {
        const div = document.createElement('div');
        div.className = 'tip-card';
        div.innerHTML = `<strong>${tip.title}</strong><p>${tip.detail}</p>`;

        // Add to Dashboard Alerts if it's a "Spike" or "High" usage
        if (tip.title.includes('Spike') || tip.title.includes('High')) {
            if (dashboardAlerts) {
                const alertDiv = div.cloneNode(true);
                alertDiv.style.borderLeft = '4px solid var(--danger)';
                dashboardAlerts.appendChild(alertDiv);
                hasAlerts = true;
            }
        }

        // Distribute to specific tabs (STRICT SEPARATION)
        // Water Tips -> Water List Only
        if (tip.title.toLowerCase().includes('water') || tip.detail.toLowerCase().includes('leak') || tip.title.includes('Plumbing')) {
            if (waterList && (tip.title.includes('Water') || tip.title.includes('Plumbing') || tip.detail.includes('water'))) {
                waterList.appendChild(div.cloneNode(true));
            }
        }
        // Energy Tips -> Energy List Only
        else if (tip.title.toLowerCase().includes('energy') || tip.detail.toLowerCase().includes('bulb') || tip.title.toLowerCase().includes('ac')) {
            if (energyList && (tip.title.includes('Energy') || tip.detail.includes('kWh'))) {
                energyList.appendChild(div.cloneNode(true));
            }
        }
        // General Tips -> Both Lists
        else {
            if (waterList) waterList.appendChild(div.cloneNode(true));
            if (energyList) energyList.appendChild(div.cloneNode(true));
        }
    });

    if (!hasAlerts && dashboardAlerts) {
        dashboardAlerts.innerHTML = '<p style="color:#888; font-style:italic;">No critical alerts. Good usage!</p>';
    }
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

    // 2. Water Chart (Daily Bar)
    const ctxWater = document.getElementById('waterChart');
    if (ctxWater && currentView === 'water') {
        if (waterChart) waterChart.destroy();
        waterChart = new Chart(ctxWater, {
            type: 'bar', // Changed to bar for daily view
            data: {
                labels: dates,
                datasets: [{
                    label: 'Water Usage (L)', // Daily
                    data: data.water_data,
                    backgroundColor: '#0288d1',
                    order: 2
                }, {
                    label: 'Daily Limit',
                    data: Array(dates.length).fill(data.water_limit),
                    borderColor: '#f44336',
                    borderDash: [5, 5],
                    type: 'line', // Line for limit
                    order: 1
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    // 3. Energy Chart (Daily Bar)
    const ctxEnergy = document.getElementById('energyChart');
    if (ctxEnergy && currentView === 'energy') {
        if (energyChart) energyChart.destroy();
        energyChart = new Chart(ctxEnergy, {
            type: 'bar', // Changed to bar for daily view
            data: {
                labels: dates,
                datasets: [{
                    label: 'Energy Usage (kWh)', // Daily
                    data: data.energy_data,
                    backgroundColor: '#fbc02d',
                    order: 2
                }, {
                    label: 'Daily Limit',
                    data: Array(dates.length).fill(data.energy_limit),
                    borderColor: '#f44336',
                    borderDash: [5, 5],
                    type: 'line', // Line for limit
                    order: 1
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
            showToast('Water entry added!', 'success');
            document.getElementById('waterUsage').value = '';
            document.getElementById('waterPreview').style.display = 'none';
            loadDashboardData();
        } else {
            showToast(data.error, 'error');
        }
    } catch (e) { showToast('Error adding entry', 'error'); }
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
            showToast('Energy entry added!', 'success');
            document.getElementById('energyUsage').value = '';
            document.getElementById('energyPreview').style.display = 'none';
            loadDashboardData();
        } else {
            showToast(data.error, 'error');
        }
    } catch (e) { showToast('Error adding entry', 'error'); }
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
        showToast('Please enter at least one limit to update.', 'warning');
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
            showToast('Limits updated successfully!', 'success');
            // Update local user object if needed, or just reload dashboard
            if (payload.custom_energy_limit !== undefined) currentUser.custom_energy_limit = payload.custom_energy_limit;
            if (payload.custom_water_limit !== undefined) currentUser.custom_water_limit = payload.custom_water_limit;
            localStorage.setItem('currentUser', JSON.stringify(currentUser));

            // Refresh data
            loadDashboardData();
        } else {
            showToast(data.error || 'Failed to update limits', 'error');
        }
    } catch (e) {
        console.error(e);
        showToast('Error updating profile', 'error');
    }
});

function downloadCSV() {
    const start = document.getElementById('reportStart').value;
    const end = document.getElementById('reportEnd').value;

    showToast('Downloading CSV report...', 'success');
    window.open(`${API_BASE}/export/${currentUser.user_id}?start_date=${start}&end_date=${end}`, '_blank');
}

// --- QUIZ & GAMIFICATION ---

let currentQuestions = [];
let userAnswers = {}; // {question_id: selected_index}

async function startQuiz() {
    try {
        const res = await fetch(`${API_BASE}/quiz/questions`);
        currentQuestions = await res.json();
        userAnswers = {};

        document.getElementById('quiz-start-screen').style.display = 'none';
        document.getElementById('quiz-result-screen').style.display = 'none';
        document.getElementById('quiz-question-screen').style.display = 'block';

        renderQuizQuestion(0);
    } catch (e) { console.error('Error starting quiz', e); }
}

function renderQuizQuestion(index) {
    if (index >= currentQuestions.length) {
        finishQuiz();
        return;
    }

    const q = currentQuestions[index];
    const total = currentQuestions.length;
    const progress = ((index) / total) * 100;

    document.getElementById('quizProgress').style.width = `${progress}%`;
    document.getElementById('questionText').textContent = q.question;

    const container = document.getElementById('optionsContainer');
    container.innerHTML = '';

    q.options.forEach((opt, idx) => {
        const btn = document.createElement('button');
        btn.className = 'btn-large btn-secondary';
        btn.style.textAlign = 'left';
        btn.textContent = opt;
        btn.onclick = () => selectOption(q.id, idx, index);
        container.appendChild(btn);
    });
}

function selectOption(qId, selectedIdx, currentIndex) {
    userAnswers[qId] = selectedIdx;
    renderQuizQuestion(currentIndex + 1);
}

async function finishQuiz() {
    document.getElementById('quizProgress').style.width = '100%';

    try {
        const res = await fetch(`${API_BASE}/quiz/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.user_id,
                answers: userAnswers
            })
        });
        const result = await res.json();

        document.getElementById('quiz-question-screen').style.display = 'none';
        document.getElementById('quiz-result-screen').style.display = 'block';

        document.getElementById('scoreDisplay').textContent = `${result.score}/${result.total}`;

        const badgeContainer = document.getElementById('newBadges');
        badgeContainer.innerHTML = '';
        if (result.achievements && result.achievements.length > 0) {
            result.achievements.forEach(name => {
                const b = document.createElement('div');
                b.className = 'badge-new';
                b.style.background = '#ffd700';
                b.style.padding = '5px 10px';
                b.style.borderRadius = '15px';
                b.style.fontWeight = 'bold';
                b.textContent = `🏆 Unlocked: ${name}`;
                badgeContainer.appendChild(b);
            });
            showToast('New Achievements Unlocked!', 'success');
        }

        loadAchievements(); // Refresh list

    } catch (e) { console.error(e); }
}

async function loadAchievements() {
    if (!currentUser) return;
    try {
        const res = await fetch(`${API_BASE}/quiz/achievements/${currentUser.user_id}`);
        const data = await res.json();

        const ptsEl = document.getElementById('totalPoints');
        if (ptsEl) ptsEl.textContent = `${data.total_points} Points`;

        const container = document.getElementById('badgesContainer');
        if (container) {
            container.innerHTML = '';

            if (data.achievements.length === 0) {
                container.innerHTML = '<p style="color:#888;">No badges yet. Play a quiz!</p>';
                return;
            }

            data.achievements.forEach(ach => {
                const div = document.createElement('div');
                div.className = 'badge-card';
                div.style.border = '1px solid #eee';
                div.style.padding = '10px';
                div.style.borderRadius = '8px';
                div.style.display = 'flex';
                div.style.alignItems = 'center';
                div.style.gap = '10px';
                // div.style.width = '100%'; // Allow wrap
                div.style.background = 'var(--bg-light)';

                div.innerHTML = `
                    <div style="font-size:2rem;">${ach.icon}</div>
                    <div>
                        <div style="font-weight:bold;">${ach.name}</div>
                        <div style="font-size:0.8rem; color:#666;">${ach.description}</div>
                    </div>
                `;
                container.appendChild(div);
            });
        }

    } catch (e) { console.error(e); }
}
