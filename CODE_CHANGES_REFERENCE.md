# Code Changes Reference

## File 1: BACKEND/app.py

### Added Lines 516-577: Dashboard Endpoint

```python
# Dashboard Endpoint - Returns weekly summary for dashboard display
@app.route('/api/dashboard/<int:user_id>', methods=['GET'])
def get_dashboard(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get data for the current week (or last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Get energy and water entries for the week
        energy_entries = EnergyEntry.query.filter(
            EnergyEntry.user_id == user_id,
            EnergyEntry.reading_date >= start_date,
            EnergyEntry.reading_date <= end_date
        ).order_by(EnergyEntry.reading_date).all()
        
        water_entries = WaterEntry.query.filter(
            WaterEntry.user_id == user_id,
            WaterEntry.reading_date >= start_date,
            WaterEntry.reading_date <= end_date
        ).order_by(WaterEntry.reading_date).all()
        
        # Calculate weekly totals
        total_energy = sum(e.electricity_usage for e in energy_entries)
        total_water = sum(w.water_usage for w in water_entries)
        total_cost = sum(e.cost for e in energy_entries) + sum(w.cost for w in water_entries)
        
        # Get user limits
        energy_limit, water_limit = get_user_limits(user)
        
        # Calculate monthly usage for full picture
        monthly_energy = get_monthly_usage(user_id, 'energy')
        monthly_water = get_monthly_usage(user_id, 'water')
        
        # Calculate percentages
        energy_percentage = (monthly_energy / energy_limit * 100) if energy_limit > 0 else 0
        water_percentage = (monthly_water / water_limit * 100) if water_limit > 0 else 0
        
        return jsonify({
            'user_id': user_id,
            'username': user.username,
            'user_category': user.user_category,
            'family_members': user.family_members,
            'total_cost': total_cost,
            'weekly_energy_used': total_energy,
            'weekly_water_used': total_water,
            'monthly_energy_used': monthly_energy,
            'monthly_water_used': monthly_water,
            'energy_limit': energy_limit,
            'water_limit': water_limit,
            'energy_percentage': energy_percentage,
            'water_percentage': water_percentage,
            'has_custom_energy_limit': user.custom_energy_limit > 0,
            'has_custom_water_limit': user.custom_water_limit > 0,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Added Lines 579-648: Chart Data Endpoint

```python
# Chart Data Endpoint - Returns data formatted for line charts showing week-by-week limits and consumption
@app.route('/api/chart-data/<int:user_id>', methods=['GET'])
def get_chart_data(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get last 7 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        energy_entries = EnergyEntry.query.filter(
            EnergyEntry.user_id == user_id,
            EnergyEntry.reading_date >= start_date,
            EnergyEntry.reading_date <= end_date
        ).order_by(EnergyEntry.reading_date).all()
        
        water_entries = WaterEntry.query.filter(
            WaterEntry.user_id == user_id,
            WaterEntry.reading_date >= start_date,
            WaterEntry.reading_date <= end_date
        ).order_by(WaterEntry.reading_date).all()
        
        # Get user limits
        energy_limit, water_limit = get_user_limits(user)
        
        # Build cumulative data arrays for the 7 days
        dates = []
        energy_data = []
        water_data = []
        cumulative_energy = 0
        cumulative_water = 0
        
        # Create 7-day timeline
        for i in range(7):
            current_day = start_date + timedelta(days=i)
            date_str = current_day.strftime('%Y-%m-%d')
            dates.append(date_str)
            
            # Get data for this day
            day_energy = sum(e.electricity_usage for e in energy_entries if e.reading_date.date() == current_day.date())
            day_water = sum(w.water_usage for w in water_entries if w.reading_date.date() == current_day.date())
            
            cumulative_energy += day_energy
            cumulative_water += day_water
            
            energy_data.append(round(cumulative_energy, 2))
            water_data.append(round(cumulative_water, 2))
        
        # Calculate when resources will end (project based on daily average)
        avg_daily_energy = cumulative_energy / 7 if cumulative_energy > 0 else 0
        avg_daily_water = cumulative_water / 7 if cumulative_water > 0 else 0
        
        energy_days_remaining = (energy_limit - cumulative_energy) / avg_daily_energy if avg_daily_energy > 0 else float('inf')
        water_days_remaining = (water_limit - cumulative_water) / avg_daily_water if avg_daily_water > 0 else float('inf')
        
        # Calculate end dates
        today = datetime.now()
        energy_end_date = (today + timedelta(days=energy_days_remaining)).strftime('%Y-%m-%d') if energy_days_remaining != float('inf') else 'Not expected to exceed'
        water_end_date = (today + timedelta(days=water_days_remaining)).strftime('%Y-%m-%d') if water_days_remaining != float('inf') else 'Not expected to exceed'
        
        # Weekly summary
        weekly_summary = [{
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'energy_total': cumulative_energy,
            'water_total': cumulative_water,
            'energy_status': 'OVER' if cumulative_energy > energy_limit else 'UNDER',
            'water_status': 'OVER' if cumulative_water > water_limit else 'UNDER'
        }]
        
        return jsonify({
            'dates': dates,
            'energy_data': energy_data,
            'water_data': water_data,
            'energy_limit': energy_limit,
            'water_limit': water_limit,
            'energy_end_date': energy_end_date,
            'water_end_date': water_end_date,
            'days_remaining_energy': round(energy_days_remaining, 1),
            'days_remaining_water': round(water_days_remaining, 1),
            'weekly_summary': weekly_summary,
            'resource_exhaustion': {
                'energy': {
                    'projected_end_date': energy_end_date,
                    'days_remaining': round(energy_days_remaining, 1),
                    'current_usage': cumulative_energy,
                    'limit': energy_limit
                },
                'water': {
                    'projected_end_date': water_end_date,
                    'days_remaining': round(water_days_remaining, 1),
                    'current_usage': cumulative_water,
                    'limit': water_limit
                }
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## File 2: FRONTEND/index.html

### Changed Chart Section (Lines ~130-160)

**FROM:**
```html
<!-- Charts Section -->
<div class="chart-container">
    <h3>📈 Usage Analytics & Trends</h3>
    <div id="usageTrendsChart" class="chart-card" style="margin-bottom:20px;"></div>
    <div class="charts-grid">
        <div class="chart-card">
            <h4>Weekly Energy Usage (kWh)</h4>
            <div id="energyUsageChart" class="chart"></div>
        </div>
        <div class="chart-card">
            <h4>Weekly Cost Trend (MWK)</h4>
            <div id="costTrendChart" class="chart"></div>
        </div>
    </div>
    <div id="monthlyBreakdown" class="breakdown-card"></div>
</div>
```

**TO:**
```html
<!-- Charts Section -->
<div class="chart-container">
    <h3>📈 Weekly Resource Consumption & Limits</h3>
    
    <!-- Resource End Date Alerts -->
    <div id="resourceEndDateAlerts" style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
        <!-- Alerts populated by JavaScript -->
    </div>
    
    <div class="charts-grid">
        <div class="chart-card">
            <h4>⚡ Energy Consumption vs Limit (7-Day Trend)</h4>
            <canvas id="energyChart"></canvas>
            <p style="font-size: 0.9rem; color: #666; margin-top: 10px;">
                Projected exhaustion: <strong id="energyEndDate">--</strong> 
                (<span id="energyDaysRemaining">--</span> days remaining)
            </p>
        </div>
        <div class="chart-card">
            <h4>💧 Water Consumption vs Limit (7-Day Trend)</h4>
            <canvas id="waterChart"></canvas>
            <p style="font-size: 0.9rem; color: #666; margin-top: 10px;">
                Projected exhaustion: <strong id="waterEndDate">--</strong> 
                (<span id="waterDaysRemaining">--</span> days remaining)
            </p>
        </div>
    </div>
    <div id="monthlyBreakdown" class="breakdown-card"></div>
</div>
```

### Changed Script Import (Lines ~248-251)

**FROM:**
```html
<script src="script.js"></script>
</body>
</html>
```

**TO:**
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="script_enhanced.js"></script>
</body>
</html>
```

---

## File 3: FRONTEND/script_enhanced.js

### Updated Lines 275-509

**Key Changes:**
1. Added global chart objects at top
2. Rewrote `loadCharts()` function
3. Completely rewrote `renderEnhancedCharts()` to use Chart.js
4. Added new `renderResourceEndDateAlerts()` function

**New Global Variables:**
```javascript
let energyChartObj = null;
let waterChartObj = null;
```

**Updated loadCharts() function:**
```javascript
async function loadCharts(data) {
    try {
        const response = await fetch(`${API_BASE}/chart-data/${currentUser.user_id}`);
        const chartData = await response.json();

        if (response.ok) {
            renderEnhancedCharts(chartData, data);
            renderWeeklySummary(chartData, data);
            renderResourceEndDateAlerts(chartData);  // NEW LINE
        }
    } catch (error) {
        console.error('Error loading charts:', error);
    }
}
```

**New renderResourceEndDateAlerts() function:**
```javascript
function renderResourceEndDateAlerts(chartData) {
    const alertsContainer = document.getElementById('resourceEndDateAlerts');
    if (!alertsContainer) return;
    
    const energyExhaustion = chartData.resource_exhaustion.energy;
    const waterExhaustion = chartData.resource_exhaustion.water;
    
    const getAlertLevel = (daysRemaining) => {
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
                <p style="margin: 5px 0;"><strong>Current Usage:</strong> ${energyExhaustion.current_usage.toFixed(1)} / ${energyExhaustion.limit} kWh</p>
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
                <p style="margin: 5px 0;"><strong>Current Usage:</strong> ${waterExhaustion.current_usage.toFixed(1)} / ${waterExhaustion.limit} L</p>
                <p style="margin: 5px 0;"><strong>Projected End Date:</strong> ${waterExhaustion.projected_end_date}</p>
                <p style="margin: 5px 0;"><strong>Days Remaining:</strong> ${waterExhaustion.days_remaining} days</p>
            </div>
        </div>
    `;
}
```

**Completely New renderEnhancedCharts() with Chart.js:**
Uses Chart.js to create two professional line charts with:
- Cumulative consumption lines
- Weekly limit reference lines (dashed)
- Interactive tooltips
- Professional styling
- Responsive design

---

## Summary of Changes

| Component | Type | Change |
|-----------|------|--------|
| Backend | Code | +130 lines (2 new endpoints) |
| HTML | Markup | Changed divs to canvas, added alerts container, added Chart.js CDN |
| JavaScript | Code | Rewrote chart rendering to use Chart.js, added alert function |
| **Total** | **Lines** | **~200+ lines added/modified** |

**Result:** Complete transition from bar graphs to professional line charts with resource exhaustion projections.
