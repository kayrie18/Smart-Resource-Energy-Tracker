const API_BASE = 'http://localhost:5000/api';

let currentUser = null;
let userCategories = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('energyDate').value = today;
    document.getElementById('waterDate').value = today;
    
    // Set default report dates (last 30 days)
    const endDate = new Date();
    const startDate = new Date(endDate.getTime() - 30 * 24 * 60 * 60 * 1000);
    document.getElementById('reportStart').value = startDate.toISOString().split('T')[0];
    document.getElementById('reportEnd').value = today;
    
    // Load user categories
    loadUserCategories();
    
    // Check if user is already logged in
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        showDashboard();
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
    
    // Show custom limits field when category is selected
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
    
    // Show custom limits field when category is selected
    if (categorySelect.value) {
        customLimitsField.style.display = 'block';
        loadProfileCategoryDefaults(categorySelect.value);
    } else {
        customLimitsField.style.display = 'none';
    }
}

// Load default limits when category is selected
async function loadCategoryDefaults(category) {
    try {
        const response = await fetch(`${API_BASE}/category-defaults/${category}`);
        const data = await response.json();
        
        document.getElementById('defaultEnergyLimit').textContent = data.default_energy_limit;
        document.getElementById('defaultWaterLimit').textContent = data.default_water_limit;
        
        // Set placeholder values
        document.getElementById('customEnergyLimit').placeholder = `Default: ${data.default_energy_limit} kWh`;
        document.getElementById('customWaterLimit').placeholder = `Default: ${data.default_water_limit} L`;
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
        
        // Set placeholder values
        document.getElementById('profileCustomEnergyLimit').placeholder = `Default: ${data.default_energy_limit} kWh`;
        document.getElementById('profileCustomWaterLimit').placeholder = `Default: ${data.default_water_limit} L`;
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

// Login
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

// Register with Custom Limits
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
        alert('Error connecting to server.');
    }
});

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
function showDashboard() {
    document.querySelector('.auth-forms').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    document.getElementById('userWelcome').textContent = currentUser.username;
    loadDashboardData();
}

async function loadDashboardData() {
    await loadAnalytics();
    await loadNotifications();
    await loadCharts();
    await loadUserProfile();
}

async function loadUserProfile() {
    try {
        const response = await fetch(`${API_BASE}/user/${currentUser.user_id}`);
        const userData = await response.json();
        
        if (response.ok) {
            // Populate profile modal
            document.getElementById('profilePhone').value = userData.phone_number || '';
            document.getElementById('profileCategory').value = userData.user_category;
            document.getElementById('profileFamilyMembers').value = userData.family_members || 1;
            document.getElementById('profileCustomEnergyLimit').value = userData.custom_energy_limit > 0 ? userData.custom_energy_limit : '';
            document.getElementById('profileCustomWaterLimit').value = userData.custom_water_limit > 0 ? userData.custom_water_limit : '';
            
            toggleProfileFamilyMembers();
            
            // Update category info display
            const categoryInfo = document.getElementById('categoryInfo');
            if (categoryInfo) {
                let infoText = `(${userData.user_category}`;
                if (userData.custom_energy_limit > 0 || userData.custom_water_limit > 0) {
                    infoText += ' - Custom Limits';
                }
                infoText += ')';
                categoryInfo.innerHTML = infoText;
            }
        }
    } catch (error) {
        console.error('Error loading user profile:', error);
    }
}

async function loadCharts() {
    try {
        const response = await fetch(`${API_BASE}/analytics/${currentUser.user_id}`);
        const data = await response.json();

        if (response.ok) {
            // Render new comprehensive usage trends graph
            renderUsageTrendsGraph(data);
            
            // Build chart data from series
            const energyData = data.series
                .filter(e => e.type === 'energy')
                .map(e => ({ date: e.date, usage: e.usage }))
                .slice(-7);
            
            const costData = data.series
                .filter(e => e.type === 'energy')
                .map(e => ({ date: e.date, cost: e.cost }))
                .slice(-7);
            
            // Render traditional charts
            renderEnergyUsageChart(energyData);
            renderCostTrendChart(costData);
            
            // Render monthly breakdown
            const breakdown = {
                energy_usage: data.total_energy,
                water_usage: data.total_water,
                total_cost: data.total_cost,
                energy_limit: data.energy_limit,
                water_limit: data.water_limit,
                default_energy_limit: data.energy_limit,
                default_water_limit: data.water_limit
            };
            renderMonthlyBreakdown(breakdown);
            
            renderMonthlyProgress(data.monthly_energy_used, data.energy_limit, data.energy_percentage, 'energy');
            renderMonthlyProgress(data.monthly_water_used, data.water_limit, data.water_percentage, 'water');
        }
    } catch (error) {
        console.error('Error loading charts:', error);
    }
}

// New function: Render comprehensive usage trends with previous period comparison
function renderUsageTrendsGraph(analyticsData) {
    const chartContainer = document.getElementById('usageTrendsChart');
    if (!chartContainer) return;
    
    const series = analyticsData.series || [];
    const prev = analyticsData.previous_period || {};
    
    // Aggregate current period by type
    let currentEnergy = 0, currentWater = 0;
    let currentEnergyCost = 0, currentWaterCost = 0;
    
    series.forEach(entry => {
        if (entry.type === 'energy') {
            currentEnergy += entry.usage;
            currentEnergyCost += entry.cost;
        } else {
            currentWater += entry.usage;
            currentWaterCost += entry.cost;
        }
    });
    
    const prevEnergy = prev.total_energy || 0;
    const prevWater = prev.total_water || 0;
    
    // Calculate trends
    const energyChange = prevEnergy > 0 ? (((currentEnergy - prevEnergy) / prevEnergy) * 100).toFixed(1) : 0;
    const waterChange = prevWater > 0 ? (((currentWater - prevWater) / prevWater) * 100).toFixed(1) : 0;
    
    const energyTrend = energyChange > 0 ? '📈 UP' : '📉 DOWN';
    const waterTrend = waterChange > 0 ? '📈 UP' : '📉 DOWN';
    
    chartContainer.innerHTML = `
        <h4>Usage Trends & Comparison</h4>
        <div class="trends-grid" style="display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-top:15px;">
            <div class="trend-card" style="padding:15px; border:1px solid #ddd; border-radius:8px; background:#f9f9f9;">
                <h5>⚡ Energy Usage</h5>
                <div style="font-size:1.5rem; font-weight:bold; color:#3498db;">${currentEnergy.toFixed(2)} kWh</div>
                <div style="font-size:0.9rem; color:#666; margin-top:5px;">
                    vs Previous: ${prevEnergy.toFixed(2)} kWh
                </div>
                <div style="font-size:1rem; margin-top:8px; color:${energyChange > 0 ? '#e74c3c' : '#27ae60'};">
                    ${energyTrend} ${Math.abs(energyChange)}%
                </div>
                <div style="font-size:0.85rem; color:#999; margin-top:5px;">
                    Cost: MWK ${currentEnergyCost.toFixed(2)}
                </div>
            </div>
            <div class="trend-card" style="padding:15px; border:1px solid #ddd; border-radius:8px; background:#f9f9f9;">
                <h5>💧 Water Usage</h5>
                <div style="font-size:1.5rem; font-weight:bold; color:#2ecc71;">${currentWater.toFixed(2)} L</div>
                <div style="font-size:0.9rem; color:#666; margin-top:5px;">
                    vs Previous: ${prevWater.toFixed(2)} L
                </div>
                <div style="font-size:1rem; margin-top:8px; color:${waterChange > 0 ? '#e74c3c' : '#27ae60'};">
                    ${waterTrend} ${Math.abs(waterChange)}%
                </div>
                <div style="font-size:0.85rem; color:#999; margin-top:5px;">
                    Cost: MWK ${currentWaterCost.toFixed(2)}
                </div>
            </div>
        </div>
        <div style="margin-top:15px; padding:10px; background:#ecf0f1; border-radius:5px; font-size:0.9rem; color:#555;">
            📅 Period: ${analyticsData.start_date} to ${analyticsData.end_date}
            | Last Update: ${analyticsData.last_update ? new Date(analyticsData.last_update).toLocaleString() : 'N/A'}
        </div>
    `;
}

function renderEnergyUsageChart(energyData) {
    const chartContainer = document.getElementById('energyUsageChart');
    if (!chartContainer || !energyData.length) {
        chartContainer.innerHTML = '<p>No energy data available</p>';
        return;
    }

    const maxUsage = Math.max(...energyData.map(d => d.usage));
    const scale = maxUsage > 0 ? 150 / maxUsage : 1;

    chartContainer.innerHTML = `
        <div class="chart-bars">
            ${energyData.map(day => `
                <div class="chart-bar-container">
                    <div class="chart-bar" style="height: ${day.usage * scale}px" title="${day.usage}kWh on ${day.date}"></div>
                    <div class="chart-label">${day.date.split('-')[2]}/${day.date.split('-')[1]}</div>
                </div>
            `).join('')}
        </div>
    `;
}

function renderCostTrendChart(costData) {
    const chartContainer = document.getElementById('costTrendChart');
    if (!chartContainer || !costData.length) {
        chartContainer.innerHTML = '<p>No cost data available</p>';
        return;
    }

    const maxCost = Math.max(...costData.map(d => d.cost));
    const scale = maxCost > 0 ? 150 / maxCost : 1;

    chartContainer.innerHTML = `
        <div class="chart-bars">
            ${costData.map(day => `
                <div class="chart-bar-container">
                    <div class="chart-bar cost-bar" style="height: ${day.cost * scale}px" title="MWK ${day.cost} on ${day.date}"></div>
                    <div class="chart-label">${day.date.split('-')[2]}/${day.date.split('-')[1]}</div>
                </div>
            `).join('')}
        </div>
    `;
}

function renderMonthlyBreakdown(breakdown) {
    const breakdownContainer = document.getElementById('monthlyBreakdown');
    if (!breakdownContainer) return;

    const customEnergyText = breakdown.energy_limit !== breakdown.default_energy_limit ? ' (Custom)' : '';
    const customWaterText = breakdown.water_limit !== breakdown.default_water_limit ? ' (Custom)' : '';

    breakdownContainer.innerHTML = `
        <h4>Monthly Summary (30 Days)</h4>
        <div class="breakdown-stats">
            <div class="breakdown-item">
                <span class="label">Energy Used:</span>
                <span class="value">${breakdown.energy_usage.toFixed(2)} kWh</span>
            </div>
            <div class="breakdown-item">
                <span class="label">Energy Limit:</span>
                <span class="value">${breakdown.energy_limit} kWh${customEnergyText}</span>
            </div>
            <div class="breakdown-item">
                <span class="label">Water Used:</span>
                <span class="value">${breakdown.water_usage.toFixed(2)} L</span>
            </div>
            <div class="breakdown-item">
                <span class="label">Water Limit:</span>
                <span class="value">${breakdown.water_limit} L${customWaterText}</span>
            </div>
            <div class="breakdown-item">
                <span class="label">Total Cost:</span>
                <span class="value">MWK ${breakdown.total_cost.toFixed(2)}</span>
            </div>
        </div>
    `;
}

function renderMonthlyProgress(used, limit, percentage, type) {
    const progressFill = document.getElementById(`${type}ProgressFill`);
    const progressText = document.getElementById(`${type}ProgressText`);
    
    if (progressFill && progressText) {
        progressFill.style.width = `${percentage}%`;
        
        // Color coding based on percentage
        if (percentage > 80) {
            progressFill.style.background = 'linear-gradient(135deg, #e74c3c, #c0392b)';
        } else if (percentage > 60) {
            progressFill.style.background = 'linear-gradient(135deg, #f39c12, #e67e22)';
        } else {
            progressFill.style.background = 'linear-gradient(135deg, #2ecc71, #27ae60)';
        }
        
        const resourceName = type === 'energy' ? 'Energy' : 'Water';
        const unit = type === 'energy' ? 'kWh' : 'L';
        progressText.innerHTML = `<strong>${resourceName}:</strong> ${used.toFixed(1)} ${unit} / ${limit} ${unit} (${percentage.toFixed(1)}%)`;
    }
}

// Updated Analytics Display
async function loadAnalytics() {
    try {
        const response = await fetch(`${API_BASE}/analytics/${currentUser.user_id}`);
        const data = await response.json();

        if (response.ok) {
            document.getElementById('energyStat').textContent = `${data.total_energy.toFixed(2)} kWh`;
            document.getElementById('waterStat').textContent = `${data.total_water.toFixed(2)} L`;
            document.getElementById('costStat').textContent = `MWK ${data.total_cost.toFixed(2)}`;
            
            // Display limits information
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
            // Show last update if available
            if (data.last_update) {
                const lu = new Date(data.last_update).toLocaleString();
                const el = document.getElementById('lastUpdate');
                if (el) el.textContent = lu;
            }
        }
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

// Download report for selected dates (CSV)
function downloadReport() {
    const start = document.getElementById('reportStart').value;
    const end = document.getElementById('reportEnd').value;
    if (!start || !end) {
        alert('Please select both start and end dates for the report.');
        return;
    }

    // Validate date range
    if (new Date(start) > new Date(end)) {
        alert('Start date must be before end date.');
        return;
    }

    const url = `${API_BASE}/report/${currentUser.user_id}?start_date=${start}&end_date=${end}&format=csv`;
    console.log('Downloading report from:', url);
    // Use browser to download
    window.open(url, '_blank');
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

        // Load and display conservation tips in dedicated section
        const analyticsResponse = await fetch(`${API_BASE}/analytics/${currentUser.user_id}`);
        const analyticsData = await analyticsResponse.json();
        
        const tipsList = document.getElementById('tipsList');
        if (tipsList && analyticsData.conservation_tips) {
            tipsList.innerHTML = '';
            analyticsData.conservation_tips.forEach(tip => {
                const tipElement = document.createElement('div');
                tipElement.style.cssText = 'padding:15px; background:white; border-radius:8px; border-left:4px solid #27ae60;';
                if (typeof tip === 'string') {
                    // Legacy string format
                    tipElement.innerHTML = `<p style="margin:0;">${tip}</p>`;
                } else if (typeof tip === 'object' && tip.title) {
                    // New structured format with title and detail
                    tipElement.innerHTML = `
                        <div style="font-weight:bold; color:#2c3e50; margin-bottom:8px;">${tip.title}</div>
                        <div style="font-size:0.95rem; color:#555; line-height:1.5;">${tip.detail}</div>
                    `;
                }
                tipsList.appendChild(tipElement);
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

// Profile Modal Functions
function showProfileModal() {
    document.getElementById('profileModal').style.display = 'block';
}

function closeProfileModal() {
    document.getElementById('profileModal').style.display = 'none';
}

// Update Profile with Custom Limits
document.getElementById('profileForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const phoneNumber = document.getElementById('profilePhone').value;
    const userCategory = document.getElementById('profileCategory').value;
    const familyMembers = document.getElementById('profileFamilyMembers').value;
    const customEnergyLimit = document.getElementById('profileCustomEnergyLimit').value;
    const customWaterLimit = document.getElementById('profileCustomWaterLimit').value;

    try {
        const response = await fetch(`${API_BASE}/user/${currentUser.user_id}/profile`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                phone_number: phoneNumber,
                user_category: userCategory,
                family_members: parseInt(familyMembers) || 1,
                custom_energy_limit: customEnergyLimit ? parseFloat(customEnergyLimit) : 0,
                custom_water_limit: customWaterLimit ? parseFloat(customWaterLimit) : 0
            })
        });

        const data = await response.json();

        if (response.ok) {
            alert(`Profile updated successfully! Your limits: Energy ${data.energy_limit} kWh, Water ${data.water_limit} L`);
            closeProfileModal();
            loadDashboardData();
        } else {
            alert(data.error || 'Failed to update profile');
        }
    } catch (error) {
        alert('Error updating profile');
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

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('profileModal');
    if (event.target === modal) {
        closeProfileModal();
    }
}