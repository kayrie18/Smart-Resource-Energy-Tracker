/**
 * Enhanced Script - Fixed Version
 * Properly displays end dates, units, and week boundaries
 */

const API_BASE = 'http://localhost:5000/api';

let currentUser = null;
let userCategories = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('energyDate').value = today;
    document.getElementById('waterDate').value = today;
    
    // Set default report dates (last 7 days for weekly tracking)
    const endDate = new Date();
    const startDate = new Date(endDate.getTime() - 7 * 24 * 60 * 60 * 1000);
    document.getElementById('reportStart').value = startDate.toISOString().split('T')[0];
    document.getElementById('reportEnd').value = today;
    
    // Display selected date range
    updateDateRangeDisplay();
    
    // Load user categories
    loadUserCategories();
    
    // Check if user is already logged in
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        showDashboard();
    }
});

// Update and display the selected date range
function updateDateRangeDisplay() {
    const startDate = document.getElementById('reportStart').value;
    const endDate = document.getElementById('reportEnd').value;
    
    if (startDate && endDate) {
        const dateRangeDisplay = document.getElementById('dateRangeDisplay');
        if (dateRangeDisplay) {
            const start = new Date(startDate);
            const end = new Date(endDate);
            const daysInRange = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
            dateRangeDisplay.innerHTML = `📅 <strong>Period:</strong> ${startDate} to ${endDate} (${daysInRange} days)`;
        }
    }
}

// Listen for date changes
document.addEventListener('change', function(e) {
    if (e.target.id === 'reportStart' || e.target.id === 'reportEnd') {
        updateDateRangeDisplay();
    }
});

// Load available user categories
async function loadUserCategories() {
    try {
        const response = await fetch(`${API_BASE}/user-categories`);
        const data = await response.json();
        userCategories = data.categories;
        
        // Populate category dropdowns
        populateCategorySelect('userCategory');
        populateCategorySelect('profileCategory');
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

function populateCategorySelect(selectId) {
    const select = document.getElementById(selectId);
    if (select) {
        select.innerHTML = '<option value="">Select User Category</option>';
        userCategories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.id;
            option.textContent = `${category.name} - ${category.description}`;
            select.appendChild(option);
        });
    }
}

// Toggle family members field based on category selection
function toggleFamilyMembers() {
    const categorySelect = document.getElementById('userCategory');
    const familyMembersField = document.getElementById('familyMembersField');
    const customLimitsField = document.getElementById('customLimitsField');
    
    if (categorySelect.value === 'family') {
        familyMembersField.style.display = 'block';
    } else {
        familyMembersField.style.display = 'none';
    }
    
    if (categorySelect.value) {
        customLimitsField.style.display = 'block';
        loadCategoryDefaults(categorySelect.value);
    } else {
        customLimitsField.style.display = 'none';
    }
}

function toggleProfileFamilyMembers() {
    const categorySelect = document.getElementById('profileCategory');
    const familyMembersField = document.getElementById('profileFamilyMembersField');
    const customLimitsField = document.getElementById('profileCustomLimitsField');
    
    if (categorySelect.value === 'family') {
        familyMembersField.style.display = 'block';
    } else {
        familyMembersField.style.display = 'none';
    }
    
    if (categorySelect.value) {
        customLimitsField.style.display = 'block';
        loadProfileCategoryDefaults(categorySelect.value);
    } else {
        customLimitsField.style.display = 'none';
    }
}

async function loadCategoryDefaults(category) {
    try {
        const response = await fetch(`${API_BASE}/category-defaults/${category}`);
        const data = await response.json();
        
        document.getElementById('defaultEnergyLimit').textContent = data.default_energy_limit;
        document.getElementById('defaultWaterLimit').textContent = data.default_water_limit;
        
        document.getElementById('customEnergyLimit').placeholder = `Default: ${data.default_energy_limit} kWh/week`;
        document.getElementById('customWaterLimit').placeholder = `Default: ${data.default_water_limit} L/week`;
    } catch (error) {
        console.error('Error loading category defaults:', error);
    }
}

async function loadProfileCategoryDefaults(category) {
    try {
        const response = await fetch(`${API_BASE}/category-defaults/${category}`);
        const data = await response.json();
        
        document.getElementById('profileDefaultEnergyLimit').textContent = data.default_energy_limit;
        document.getElementById('profileDefaultWaterLimit').textContent = data.default_water_limit;
        
        document.getElementById('profileCustomEnergyLimit').placeholder = `Default: ${data.default_energy_limit} kWh/week`;
        document.getElementById('profileCustomWaterLimit').placeholder = `Default: ${data.default_water_limit} L/week`;
    } catch (error) {
        console.error('Error loading category defaults:', error);
    }
}

// Auth functions
function showRegister() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
}

function showLogin() {
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('login-form').style.display = 'block';
}

// ===== LOGIN =====
document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            currentUser = data;
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            showDashboard();
        } else {
            alert(data.error || 'Login failed');
        }
    } catch (error) {
        alert('Error connecting to server. Make sure backend is running on port 5000.');
    }
});

// ===== REGISTER =====
document.getElementById('registerForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const phoneNumber = document.getElementById('regPhone').value;
    const userCategory = document.getElementById('userCategory').value;
    const familyMembers = document.getElementById('familyMembers').value;
    const customEnergyLimit = document.getElementById('customEnergyLimit').value;
    const customWaterLimit = document.getElementById('customWaterLimit').value;

    try {
        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                username, 
                email, 
                password,
                phone_number: phoneNumber,
                user_category: userCategory,
                family_members: parseInt(familyMembers) || 1,
                custom_energy_limit: customEnergyLimit ? parseFloat(customEnergyLimit) : 0,
                custom_water_limit: customWaterLimit ? parseFloat(customWaterLimit) : 0
            })
        });

        const data = await response.json();

        if (response.ok) {
            alert('Registration successful! Please login.');
            showLogin();
        } else {
            alert(data.error || 'Registration failed');
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
});

function showDashboard() {
    document.querySelector('.auth-forms').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    
    document.getElementById('userWelcome').textContent = currentUser.username;
    
    loadDashboardData();
    loadNotifications();
}

async function loadDashboardData() {
    try {
        const response = await fetch(`${API_BASE}/dashboard/${currentUser.user_id}`);
        const data = await response.json();

        if (response.ok) {
            // Update stats
            document.getElementById('energyStat').textContent = `${data.monthly_energy_used.toFixed(2)} kWh/week`;
            document.getElementById('waterStat').textContent = `${data.monthly_water_used.toFixed(2)} L/week`;
            document.getElementById('costStat').textContent = `MWK ${data.total_cost.toFixed(2)}`;
            
            document.getElementById('categoryInfo').textContent = `[${data.user_category.toUpperCase()}]`;
            
            if (data.user_category === 'family') {
                document.getElementById('categoryInfo').textContent += ` (${data.family_members} members)`;
            }
            
            // Update progress bars
            const energyPercentage = Math.min(data.energy_percentage, 100);
            const waterPercentage = Math.min(data.water_percentage, 100);
            
            const energyFill = document.getElementById('energyProgressFill');
            const waterFill = document.getElementById('waterProgressFill');
            const energyText = document.getElementById('energyProgressText');
            const waterText = document.getElementById('waterProgressText');
            
            if (energyFill) {
                energyFill.style.width = energyPercentage + '%';
                energyFill.style.backgroundColor = energyPercentage > 80 ? '#e74c3c' : (energyPercentage > 50 ? '#f39c12' : '#27ae60');
            }
            if (waterFill) {
                waterFill.style.width = waterPercentage + '%';
                waterFill.style.backgroundColor = waterPercentage > 80 ? '#e74c3c' : (waterPercentage > 50 ? '#f39c12' : '#27ae60');
            }
            if (energyText) {
                energyText.innerHTML = `${data.monthly_energy_used.toFixed(1)} / ${data.energy_limit} kWh (${energyPercentage.toFixed(0)}%)`;
            }
            if (waterText) {
                waterText.innerHTML = `${data.monthly_water_used.toFixed(1)} / ${data.water_limit} L (${waterPercentage.toFixed(0)}%)`;
            }
            
            loadCharts(data);
            loadAnalytics();
            loadUserProfile();
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Global chart objects for updating
let energyChartObj = null;
let waterChartObj = null;

async function loadCharts(data) {
    try {
        console.log('loadCharts called - fetching chart data for user:', currentUser.user_id);
        const response = await fetch(`${API_BASE}/chart-data/${currentUser.user_id}`);
        const chartData = await response.json();

        console.log('Chart data received:', chartData);
        console.log('Response ok:', response.ok);

        if (response.ok) {
            console.log('Calling renderEnhancedCharts with:', chartData);
            renderEnhancedCharts(chartData, data);
            renderWeeklySummary(chartData, data);
            renderResourceEndDateAlerts(chartData);
        } else {
            console.error('Chart data response not ok:', response.status, chartData);
        }
    } catch (error) {
        console.error('Error loading charts:', error);
    }
}

// ===== ENHANCED CHART RENDERING WITH CHART.JS =====
function renderEnhancedCharts(chartData, dashboardData) {
    console.log('renderEnhancedCharts called');
    const energyCtx = document.getElementById('energyChart');
    const waterCtx = document.getElementById('waterChart');
    
    console.log('Canvas elements found:', !!energyCtx, !!waterCtx);
    
    if (!energyCtx || !waterCtx) {
        console.error('Canvas elements not found in DOM');
        return;
    }
    
    const dates = chartData.dates || [];
    const energyData = chartData.energy_data || [];
    const waterData = chartData.water_data || [];
    
    console.log('Chart data structure:', {
        dates: dates.length,
        energyData: energyData.length,
        waterData: waterData.length,
        energyLimit: chartData.energy_limit,
        waterLimit: chartData.water_limit
    });
    
    const energyLimit = chartData.energy_limit;
    const waterLimit = chartData.water_limit;
    
    // Energy Chart
    if (energyChartObj) {
        energyChartObj.destroy();
    }
    
    try {
        energyChartObj = new Chart(energyCtx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Energy Consumption (Cumulative)',
                    data: energyData,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 6,
                    pointBackgroundColor: '#3498db',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverRadius: 8
                },
                {
                    label: `Weekly Limit (${energyLimit} kWh)`,
                    data: Array(dates.length).fill(energyLimit),
                    borderColor: '#e74c3c',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0,
                    tension: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: { size: 12, weight: 'bold' },
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleFont: { size: 14, weight: 'bold' },
                    bodyFont: { size: 12 },
                    padding: 12,
                    borderRadius: 5,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += context.parsed.y.toFixed(2) + ' kWh';
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Date',
                        font: { size: 12, weight: 'bold' }
                    },
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Energy (kWh)',
                        font: { size: 12, weight: 'bold' }
                    },
                    beginAtZero: true,
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });
    console.log('Energy chart created successfully');
    } catch (error) {
        console.error('Error creating energy chart:', error);
    }
    
    // Water Chart
    if (waterChartObj) {
        waterChartObj.destroy();
    }
    
    try {
        waterChartObj = new Chart(waterCtx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Water Consumption (Cumulative)',
                    data: waterData,
                    borderColor: '#2ecc71',
                    backgroundColor: 'rgba(46, 204, 113, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 6,
                    pointBackgroundColor: '#2ecc71',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverRadius: 8
                },
                {
                    label: `Weekly Limit (${waterLimit} L)`,
                    data: Array(dates.length).fill(waterLimit),
                    borderColor: '#e74c3c',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0,
                    tension: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: { size: 12, weight: 'bold' },
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleFont: { size: 14, weight: 'bold' },
                    bodyFont: { size: 12 },
                    padding: 12,
                    borderRadius: 5,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += context.parsed.y.toFixed(2) + ' L';
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Date',
                        font: { size: 12, weight: 'bold' }
                    },
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Water (Liters)',
                        font: { size: 12, weight: 'bold' }
                    },
                    beginAtZero: true,
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });
    console.log('Water chart created successfully');
    } catch (error) {
        console.error('Error creating water chart:', error);
    }
    
    // Update end date information
    console.log('Updating end date information');
    document.getElementById('energyEndDate').textContent = chartData.energy_end_date;
    document.getElementById('waterEndDate').textContent = chartData.water_end_date;
    document.getElementById('energyDaysRemaining').textContent = chartData.days_remaining_energy;
    document.getElementById('waterDaysRemaining').textContent = chartData.days_remaining_water;
    
    // Add days elapsed/remaining information
    const daysElapsed = chartData.days_elapsed || 0;
    const daysRemaining = chartData.days_remaining_in_week || 7;
    document.getElementById('energyDaysInfo').textContent = `Day ${daysElapsed + 1} of 7 (${daysRemaining} days left in week)`;
    document.getElementById('waterDaysInfo').textContent = `Day ${daysElapsed + 1} of 7 (${daysRemaining} days left in week)`;
    
    console.log('renderEnhancedCharts completed successfully');
}

// ===== RESOURCE END DATE ALERTS =====
function renderResourceEndDateAlerts(chartData) {
    const alertsContainer = document.getElementById('resourceEndDateAlerts');
    if (!alertsContainer) return;
    
    const energyExhaustion = chartData.resource_exhaustion.energy;
    const waterExhaustion = chartData.resource_exhaustion.water;
    
    // Determine alert levels
    const getAlertLevel = (daysRemaining) => {
        if (typeof daysRemaining === 'string') return { level: 'safe', icon: '🟢', text: 'OK' };
        if (daysRemaining <= 0) return { level: 'critical', icon: '🔴', text: 'CRITICAL' };
        if (daysRemaining <= 1) return { level: 'urgent', icon: '🟠', text: 'URGENT' };
        if (daysRemaining <= 3) return { level: 'warning', icon: '🟡', text: 'WARNING' };
        return { level: 'safe', icon: '🟢', text: 'OK' };
    };
    
    const energyAlert = getAlertLevel(energyExhaustion.days_remaining);
    const waterAlert = getAlertLevel(waterExhaustion.days_remaining);
    
    alertsContainer.innerHTML = `
        <div style="padding: 15px; background: linear-gradient(135deg, #3498db, #2980b9); color: white; border-radius: 8px; border-left: 5px solid #1abc9c;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <span style="font-size: 1.5rem;">${energyAlert.icon}</span>
                <strong style="font-size: 1.1rem;">Energy Resource Status: ${energyAlert.text}</strong>
            </div>
            <div style="font-size: 0.95rem; line-height: 1.6; margin-left: 35px;">
                <p style="margin: 5px 0;"><strong>Weekly Usage:</strong> ${energyExhaustion.current_usage.toFixed(1)} / ${energyExhaustion.weekly_limit.toFixed(1)} kWh</p>
                <p style="margin: 5px 0;"><strong>Monthly Limit:</strong> ${energyExhaustion.monthly_limit} kWh</p>
                <p style="margin: 5px 0;"><strong>Projected End Date:</strong> ${energyExhaustion.projected_end_date}</p>
                <p style="margin: 5px 0;"><strong>Days Remaining:</strong> ${energyExhaustion.days_remaining} days</p>
            </div>
        </div>
        
        <div style="padding: 15px; background: linear-gradient(135deg, #2ecc71, #27ae60); color: white; border-radius: 8px; border-left: 5px solid #16a085;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <span style="font-size: 1.5rem;">${waterAlert.icon}</span>
                <strong style="font-size: 1.1rem;">Water Resource Status: ${waterAlert.text}</strong>
            </div>
            <div style="font-size: 0.95rem; line-height: 1.6; margin-left: 35px;">
                <p style="margin: 5px 0;"><strong>Weekly Usage:</strong> ${waterExhaustion.current_usage.toFixed(1)} / ${waterExhaustion.weekly_limit.toFixed(1)} L</p>
                <p style="margin: 5px 0;"><strong>Monthly Limit:</strong> ${waterExhaustion.monthly_limit} L</p>
                <p style="margin: 5px 0;"><strong>Projected End Date:</strong> ${waterExhaustion.projected_end_date}</p>
                <p style="margin: 5px 0;"><strong>Days Remaining:</strong> ${waterExhaustion.days_remaining} days</p>
            </div>
        </div>
    `;
}

// ===== WEEKLY SUMMARY DISPLAY =====
function renderWeeklySummary(chartData, dashboardData) {
    const summaryContainer = document.getElementById('weeklySummary');
    if (!summaryContainer) return;
    
    const weeklySummaries = chartData.weekly_summary || [];
    
    if (weeklySummaries.length === 0) {
        summaryContainer.innerHTML = '<p>No weekly data available yet.</p>';
        return;
    }
    
    const summaryHTML = weeklySummaries.map((week, idx) => {
        const weeklyEnergyLimit = chartData.energy_limit;
        const weeklyWaterLimit = chartData.water_limit;
        const waterStatus = week.water_total > weeklyWaterLimit ? '❌ OVER' : '✅ UNDER';
        const energyStatus = week.energy_total > weeklyEnergyLimit ? '❌ OVER' : '✅ UNDER';
        
        return `
            <div style="padding: 12px; background: #f9f9f9; border-left: 4px solid #3498db; margin-bottom: 10px; border-radius: 4px;">
                <strong>📅 Week ${idx + 1}: ${week.start_date} to ${week.end_date} (Day ${week.days_elapsed + 1} of 7)</strong><br>
                <small>💧 Water: <strong>${week.water_total.toFixed(0)} L</strong> / ${weeklyWaterLimit.toFixed(0)} L/week ${waterStatus}</small><br>
                <small>⚡ Electricity: <strong>${week.energy_total.toFixed(0)} kWh</strong> / ${weeklyEnergyLimit.toFixed(0)} kWh/week ${energyStatus}</small>
            </div>
        `;
    }).join('');
    
    summaryContainer.innerHTML = `<h4>📊 Weekly Breakdown</h4>${summaryHTML}`;
}

// Download report with proper date range display
function downloadReport() {
    const start = document.getElementById('reportStart').value;
    const end = document.getElementById('reportEnd').value;
    
    if (!start || !end) {
        alert('Please select both start and end dates for the report.');
        return;
    }

    if (new Date(start) > new Date(end)) {
        alert('Start date must be before end date.');
        return;
    }

    alert(`📥 Downloading report for period: ${start} to ${end}`);
    
    const url = `${API_BASE}/report/${currentUser.user_id}?start_date=${start}&end_date=${end}&format=csv`;
    window.open(url, '_blank');
}

async function loadAnalytics() {
    try {
        const response = await fetch(`${API_BASE}/analytics/${currentUser.user_id}`);
        const data = await response.json();

        if (response.ok) {
            const limitsInfo = document.getElementById('limitsInfo');
            if (limitsInfo) {
                let limitsText = '';
                if (data.has_custom_energy_limit || data.has_custom_water_limit) {
                    limitsText = '<small>Using Custom Limits</small>';
                } else {
                    limitsText = '<small>Using Default Limits</small>';
                }
                limitsInfo.innerHTML = limitsText;
            }
            
            if (data.last_update) {
                const lu = new Date(data.last_update).toLocaleString();
                const el = document.getElementById('lastUpdate');
                if (el) el.textContent = lu;
            }
            
            // Load conservation tips
            const tipsList = document.getElementById('tipsList');
            if (tipsList && data.conservation_tips) {
                tipsList.innerHTML = '';
                data.conservation_tips.forEach(tip => {
                    const tipElement = document.createElement('div');
                    tipElement.style.cssText = 'padding:15px; background:white; border-radius:8px; border-left:4px solid #27ae60;';
                    if (typeof tip === 'string') {
                        tipElement.innerHTML = `<p style="margin:0;">${tip}</p>`;
                    } else if (typeof tip === 'object' && tip.title) {
                        tipElement.innerHTML = `
                            <div style="font-weight:bold; color:#2c3e50; margin-bottom:8px;">${tip.title}</div>
                            <div style="font-size:0.95rem; color:#555; line-height:1.5;">${tip.detail}</div>
                        `;
                    }
                    tipsList.appendChild(tipElement);
                });
            }
        }
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

async function loadNotifications() {
    try {
        const response = await fetch(`${API_BASE}/notifications/${currentUser.user_id}`);
        const notifications = await response.json();

        const notificationsList = document.getElementById('notificationsList');
        notificationsList.innerHTML = '';

        if (notifications.length === 0) {
            notificationsList.innerHTML = '<div class="notification-item info"><p>No new notifications - Keep up the good work!</p></div>';
        } else {
            notifications.forEach(notification => {
                const notificationElement = document.createElement('div');
                notificationElement.className = `notification-item ${notification.type}`;
                const smsBadge = notification.sms_sent ? ' 📱' : '';
                notificationElement.innerHTML = `
                    <p>${notification.message}${smsBadge}</p>
                    <small>${new Date(notification.created_at).toLocaleDateString()}</small>
                    <button onclick="markNotificationRead(${notification.id})" style="float: right; padding: 5px 10px; font-size: 12px;">Dismiss</button>
                `;
                notificationsList.appendChild(notificationElement);
            });
        }
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

async function markNotificationRead(notificationId) {
    try {
        await fetch(`${API_BASE}/notifications/${notificationId}/read`, {
            method: 'PUT'
        });
        loadNotifications();
    } catch (error) {
        console.error('Error marking notification as read:', error);
    }
}

// Add Energy Entry
document.getElementById('energyForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const electricityUsage = parseFloat(document.getElementById('electricityUsage').value);
    const readingDate = document.getElementById('energyDate').value;

    // Validate input
    if (isNaN(electricityUsage) || electricityUsage <= 0) {
        alert('Please enter a valid electricity usage greater than 0');
        return;
    }
    if (!readingDate) {
        alert('Please select a reading date');
        return;
    }

    try {
        // Preview cost first
        const previewResp = await fetch(`${API_BASE}/preview/energy`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ user_id: currentUser.user_id, electricity_usage: electricityUsage, reading_date: readingDate })
        });
        const preview = await previewResp.json();
        if (!previewResp.ok) {
            alert(preview.error || 'Error previewing energy cost');
            return;
        }

        let confirmText = `Preview cost: MWK ${preview.calculated_cost}\nProjected monthly total: ${preview.projected_monthly_total} kWh`;
        if (preview.warning) confirmText += `\nWARNING: ${preview.warning}`;
        confirmText += '\n\nSubmit this energy reading and save to database?';

        if (!confirm(confirmText)) return;

        // If confirmed, submit entry
        const response = await fetch(`${API_BASE}/energy-entries`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ user_id: currentUser.user_id, electricity_usage: electricityUsage, reading_date: readingDate })
        });
        const data = await response.json();
        if (response.ok) {
            alert(`Energy entry added successfully! Cost: MWK ${data.calculated_cost}`);
            document.getElementById('energyForm').reset();
            document.getElementById('energyDate').value = new Date().toISOString().split('T')[0];
            loadDashboardData();
        } else {
            alert(data.error || 'Failed to add energy entry');
        }
    } catch (error) {
        alert('Error connecting to server');
    }
});

// Add Water Entry (now with auto cost calculation)
document.getElementById('waterForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const waterUsage = parseFloat(document.getElementById('waterUsage').value);
    const readingDate = document.getElementById('waterDate').value;

    // Validate input
    if (isNaN(waterUsage) || waterUsage <= 0) {
        alert('Please enter a valid water usage greater than 0');
        return;
    }
    if (!readingDate) {
        alert('Please select a reading date');
        return;
    }

    try {
        // Preview water cost first
        const previewResp = await fetch(`${API_BASE}/preview/water`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ user_id: currentUser.user_id, water_usage: waterUsage, reading_date: readingDate })
        });
        const preview = await previewResp.json();
        if (!previewResp.ok) {
            alert(preview.error || 'Error previewing water cost');
            return;
        }

        let confirmText = `Preview cost: MWK ${preview.calculated_cost}\nProjected monthly total: ${preview.projected_monthly_total} L`;
        if (preview.warning) confirmText += `\nWARNING: ${preview.warning}`;
        confirmText += '\n\nSubmit this water reading and save to database?';

        if (!confirm(confirmText)) return;

        // If confirmed, submit entry
        const response = await fetch(`${API_BASE}/water-entries`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ user_id: currentUser.user_id, water_usage: waterUsage, reading_date: readingDate })
        });
        const data = await response.json();
        if (response.ok) {
            alert(`Water entry added successfully! Cost: MWK ${data.calculated_cost}`);
            document.getElementById('waterForm').reset();
            document.getElementById('waterDate').value = new Date().toISOString().split('T')[0];
            loadDashboardData();
        } else {
            alert(data.error || 'Failed to add water entry');
        }
    } catch (error) {
        alert('Error connecting to server');
    }
});

// Dashboard functions

// Load user profile data for the profile modal
async function loadUserProfile() {
    try {
        const response = await fetch(`${API_BASE}/user/${currentUser.user_id}`);
        const user = await response.json();

        if (response.ok) {
            // Populate profile form
            document.getElementById('profilePhone').value = user.phone_number || '';
            document.getElementById('profileCategory').value = user.user_category || 'single';
            document.getElementById('profileFamilyMembers').value = user.family_members || 1;
            document.getElementById('profileCustomEnergyLimit').value = user.custom_energy_limit > 0 ? user.custom_energy_limit : '';
            document.getElementById('profileCustomWaterLimit').value = user.custom_water_limit > 0 ? user.custom_water_limit : '';
            
            // Show/hide family members field
            toggleProfileFamilyMembers();
        }
    } catch (error) {
        console.error('Error loading user profile:', error);
    }
}

// Profile Modal Functions
function showProfileModal() {
    // Load latest profile data before showing modal
    loadUserProfile();
    document.getElementById('profileModal').style.display = 'block';
}

function closeProfileModal() {
    document.getElementById('profileModal').style.display = 'none';
}

// Toggle family members field visibility
function toggleProfileFamilyMembers() {
    const category = document.getElementById('profileCategory').value;
    const familyField = document.getElementById('profileFamilyMembersField');
    if (category === 'family') {
        familyField.style.display = 'block';
    } else {
        familyField.style.display = 'none';
    }
}

// Update Profile
document.getElementById('profileForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const phoneNumber = document.getElementById('profilePhone').value;
    const userCategory = document.getElementById('profileCategory').value;
    const familyMembers = document.getElementById('profileFamilyMembers').value;
    const customEnergyLimit = document.getElementById('profileCustomEnergyLimit').value;
    const customWaterLimit = document.getElementById('profileCustomWaterLimit').value;
    
    if (!userCategory) {
        alert('Please select a user category');
        return;
    }
    
    const fam = parseInt(familyMembers);
    if (isNaN(fam) || fam < 1) {
        alert('Family members must be at least 1');
        return;
    }
    
    if (customEnergyLimit && isNaN(parseFloat(customEnergyLimit))) {
        alert('Energy limit must be a valid number');
        return;
    }
    
    if (customWaterLimit && isNaN(parseFloat(customWaterLimit))) {
        alert('Water limit must be a valid number');
        return;
    }
    
    // Get default limits for this category
    const defaults = {
        'single': { energy: 100, water: 5000 },
        'family': { energy: 300, water: 15000 },
        'hostel': { energy: 1000, water: 50000 },
        'company': { energy: 5000, water: 100000 }
    };
    const defaultEnergy = defaults[userCategory]?.energy || 100;
    const defaultWater = defaults[userCategory]?.water || 5000;
    
    // Validate custom limits don't exceed defaults
    if (customEnergyLimit) {
        const customE = parseFloat(customEnergyLimit);
        if (customE > defaultEnergy) {
            alert(`Custom energy limit (${customE} kWh) cannot exceed default limit (${defaultEnergy} kWh) for ${userCategory} category`);
            return;
        }
        if (customE <= 0) {
            alert('Custom energy limit must be greater than 0');
            return;
        }
    }
    
    if (customWaterLimit) {
        const customW = parseFloat(customWaterLimit);
        if (customW > defaultWater) {
            alert(`Custom water limit (${customW} L) cannot exceed default limit (${defaultWater} L) for ${userCategory} category`);
            return;
        }
        if (customW <= 0) {
            alert('Custom water limit must be greater than 0');
            return;
        }
    }

    try {
        const response = await fetch(`${API_BASE}/user/${currentUser.user_id}/profile`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                phone_number: phoneNumber,
                user_category: userCategory,
                family_members: fam,
                custom_energy_limit: customEnergyLimit ? parseFloat(customEnergyLimit) : 0,
                custom_water_limit: customWaterLimit ? parseFloat(customWaterLimit) : 0
            })
        });

        const data = await response.json();

        if (response.ok) {
            alert(`Profile updated! Limits: ${data.energy_limit} kWh/week, ${data.water_limit} L/week`);
            closeProfileModal();
            loadDashboardData();
            loadUserProfile();
        } else {
            alert(`Error: ${data.error || 'Failed to update profile'}`);
        }
    } catch (error) {
        console.error('Profile update error:', error);
        alert(`Error: ${error.message}`);
    }
});

function logout() {
    currentUser = null;
    localStorage.removeItem('currentUser');
    document.getElementById('dashboard').style.display = 'none';
    document.querySelector('.auth-forms').style.display = 'block';
    showLogin();
    
    document.getElementById('loginForm').reset();
    document.getElementById('registerForm').reset();
}

window.onclick = function(event) {
    const modal = document.getElementById('profileModal');
    if (event.target === modal) {
        closeProfileModal();
    }
}
