# Visual Guide - Resource Exhaustion Charts

## What You'll See Now

### 1. Resource End Date Alerts (Top of Dashboard)
Two cards showing real-time resource status with color-coded alerts:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 Energy Resource Status: CRITICAL
   Current Usage: 95 / 100 kWh
   Projected End Date: 2025-11-23
   Days Remaining: 0.5 days
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 Water Resource Status: OK
   Current Usage: 3500 / 5000 L
   Projected End Date: 2025-12-10
   Days Remaining: 5.2 days
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 2. Energy Chart - Line Graph
Shows cumulative energy consumption over 7 days with weekly limit line:

```
Energy (kWh)
    |
100 |                 ╱─ ─ ─ LIMIT (100 kWh)
    |                ╱
 80 |           ╱─────
    |         ╱ 
 60 |       ╱
    |     ╱
 40 |   ●
    | ╱
 20 |●─────●─────●
    |
  0 |_____________
    Day1  Day2  Day3  Day4  Day5  Day6  Day7

Projected exhaustion: 2025-11-23
Days remaining: 0.5 days
```

### 3. Water Chart - Line Graph
Shows cumulative water consumption over 7 days with weekly limit line:

```
Water (Liters)
      |
 5000 |                 ╱─ ─ ─ LIMIT (5000 L)
      |                ╱
 4000 |           ╱─────
      |         ╱ 
 3000 |       ●
      |     ╱
 2000 |   ●
      | ╱
 1000 |●─────●─────●
      |
    0 |_____________
      Day1  Day2  Day3  Day4  Day5  Day6  Day7

Projected exhaustion: 2025-12-10
Days remaining: 5.2 days
```

## Alert Status Meanings

### 🟢 GREEN - OK (> 3 days remaining)
- No immediate action needed
- Current consumption rate is sustainable
- Resources will last comfortably through the week

### 🟡 YELLOW - WARNING (1-3 days remaining)
- Pay attention to your consumption
- Consider reducing usage
- Resources will run out soon

### 🟠 ORANGE - URGENT (≤ 1 day remaining)
- Take immediate action to reduce consumption
- Resources will be exhausted within 24 hours
- Urgent conservation measures recommended

### 🔴 RED - CRITICAL (≤ 0 days remaining)
- Resources already exceeded or will exceed today
- Immediate action required
- Implement emergency conservation protocols

## Interactive Features

**Hover over chart points to see:**
- Exact date
- Exact consumption value (kWh or L)
- Distance from limit

**Example tooltip when hovering over a point:**
```
┌─────────────────────────────────┐
│ 2025-11-20                      │
│ Energy Consumption: 45.32 kWh   │
│ Weekly Limit: 100 kWh           │
└─────────────────────────────────┘
```

## How Projections Are Calculated

The system analyzes your 7-day consumption pattern:

1. **Calculate daily average**: Total consumption ÷ 7 days
2. **Calculate remaining**: Weekly limit - Current consumption
3. **Project end date**: Today + (Remaining ÷ Daily average)

### Example:
- Current consumption: 70 kWh in 7 days
- Daily average: 70 ÷ 7 = 10 kWh/day
- Weekly limit: 100 kWh
- Remaining: 100 - 70 = 30 kWh
- Days remaining: 30 ÷ 10 = 3 days
- Projected end date: Today + 3 days

## What Happens When You Add New Data

1. ✓ Submit new energy/water entry
2. ✓ System calculates new totals
3. ✓ Charts automatically update
4. ✓ Projections recalculate
5. ✓ Alert status refreshes

No manual refresh needed - everything updates instantly!

## Tips for Using Charts

1. **Check daily**: Monitor your consumption trend
2. **Act early**: Don't wait for red alerts
3. **Plan ahead**: Use projections to plan your week
4. **Track patterns**: Notice your usage habits
5. **Optimize**: Adjust behavior based on trends

## Customizing Your Limits

If projections show resources ending too soon:
1. Click "Update Profile & Custom Limits"
2. Set custom energy/water limits
3. Charts will recalculate based on new limits
4. See how your consumption compares

## Week Definition

- **Week**: Last 7 consecutive days
- **Current**: Today's consumption included
- **Resets**: Chart shows rolling 7-day window
- **Updates**: Every time data is added or refreshed

---

**Charts are live and update in real-time as you add consumption entries!**
