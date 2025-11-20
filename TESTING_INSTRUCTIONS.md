# Testing Instructions - Resource Management System

## Pre-Test Setup ✅
- Database has been reset with 4 test accounts
- All code changes have been deployed
- Backend and Frontend servers are running

## Test Accounts Available

```
Account 1 (Single User - Custom Limits)
  Username: john_doe
  Password: password123
  Category: Single
  Limits: 80 kWh/month, 4000 L/month
  Weekly: 20 kWh/week, 1000 L/week

Account 2 (Family - Default Limits)
  Username: family_banda
  Password: password123
  Category: Family (4 members)
  Limits: 1200 kWh/month, 60000 L/month
  Weekly: 300 kWh/week, 15000 L/week

Account 3 (Hostel)
  Username: hostel_mgr
  Password: password123
  Category: Hostel
  Limits: 1200 kWh/month (custom - cannot exceed 1000)

Account 4 (Very Low Limits)
  Username: custom_user
  Password: password123
  Category: Single
  Limits: 50 kWh/month, 2000 L/month
  Weekly: 12.5 kWh/week, 500 L/week
```

---

## Test Scenario 1: Verify Limit Enforcement

### Step 1: Edit Profile Limits
1. Log in as **john_doe**
2. Click "👤 View/Edit Profile"
3. In "Custom Monthly Limits" section:
   - Try to set Energy Limit to **90 kWh** (exceeds 80 kWh default)
   - Should see error: "Custom energy limit (90 kWh) cannot exceed default limit (80 kWh)"
   - Try to set Water Limit to **5000 L** (exceeds 4000 L default)
   - Should see error: "Custom water limit (5000 L) cannot exceed default limit (4000 L)"

### Expected Result: ✅
- Cannot save limits that exceed the default for the user category
- Clear error messages show the allowed maximum

---

## Test Scenario 2: Weekly Limits Display Correctly

### Step 1: View Charts
1. Log in as **custom_user** (very low limits for quick demonstration)
2. Look at the **"📈 Weekly Resource Consumption & Limits"** section
3. Charts should show:
   - Energy chart with limit line at **12.5 kWh** (not 50 kWh)
   - Water chart with limit line at **500 L** (not 2000 L)
   - X-axis dates in **MM-DD** format (e.g., "11-20")

### Expected Result: ✅
- Limit lines on charts show WEEKLY limits (monthly ÷ 4)
- Easier to read and compare 7-day consumption against proper weekly targets

---

## Test Scenario 3: Days Information Display

### Step 1: Check Resource Status Alerts
1. Log in as **john_doe**
2. Look at the alert boxes below charts
3. Should show:
   - **"📅 Week 1: YYYY-MM-DD to YYYY-MM-DD (Day X of 7)"**
   - Weekly usage: "X kWh / 20 kWh" (not 80 kWh)
   - Projected end date based on weekly consumption rate

### Expected Result: ✅
- Users can see which day of the week period they're in
- Limits shown are weekly, not monthly
- Consistent with chart display

---

## Test Scenario 4: Cannot Exceed Monthly Limit

### Step 1: Try to Exceed Limit
1. Log in as **custom_user** (50 kWh limit)
2. Scroll to **"⚡ Add Energy Reading"** form
3. Enter:
   - Electricity Usage: **55 kWh**
   - Reading Date: Today
4. Click **"Preview Cost"** (or "Add" if it auto-previews)
5. Should see error: "Adding this entry would exceed your monthly energy limit. You have X kWh remaining."

### Step 2: Add Valid Entry
1. Log in as **john_doe** (80 kWh limit)
2. Check current monthly usage in dashboard
3. Enter an amount that leaves some capacity
4. Confirm preview and save
5. Dashboard should update immediately

### Expected Result: ✅
- Cannot save entries that exceed monthly limit
- Clear error message showing remaining capacity
- Dashboard updates after successful entry

---

## Test Scenario 5: Alerts & Notifications Update

### Step 1: Add Multiple Entries to Trigger Alerts
1. Log in as **custom_user** (quickest to see alerts)
2. Add entries:
   - 5 kWh (Total: 5 - GREEN ✅)
   - 3 kWh (Total: 8 - GREEN ✅)
   - 3 kWh (Total: 11 - YELLOW ⚠️ - warning at 80% of 12.5)
   - 1.5 kWh (Total: 12.5 - RED 🔴 - exceeded weekly limit)

### Step 2: Check Alert Status
1. Each time you add data, dashboard should refresh
2. Alert colors should change based on usage percentage:
   - **Green 🟢**: < 50% of weekly limit
   - **Yellow 🟡**: 50-80% of weekly limit  
   - **Orange 🟠**: 80%+ but not exceeded
   - **Red 🔴**: Exceeded weekly limit

### Expected Result: ✅
- Alerts update in real-time after each entry
- Colors accurately reflect usage percentage
- Weekly limits used for calculation (not monthly)

---

## Test Scenario 6: All Accounts Behave Consistently

### Test with Multiple Accounts
1. Log in as **john_doe** → Add 15 kWh → Charts show against 20 kWh weekly limit
2. Log out, log in as **family_banda** → Add 250 kWh → Charts show against 300 kWh weekly limit
3. Log out, log in as **custom_user** → Add 10 kWh → Charts show against 12.5 kWh weekly limit

### Check Consistency
- All accounts should have same calculation logic
- All should show weekly limits on charts
- All should have same validation rules
- No test account vs. new account differences

### Expected Result: ✅
- Identical behavior across all test accounts
- No inconsistencies or special cases

---

## Test Scenario 7: Create New Account & Test

### Step 1: Register New User
1. Go to **Register** tab
2. Create new account:
   - Username: testuser123
   - Email: test@example.com
   - Password: password123
   - Phone: +265991234567
3. Login with new account

### Step 2: Set Profile
1. Click "👤 View/Edit Profile"
2. Select Category: **"Family"**
3. Set Family Members: **2**
4. Set Custom Limits: Leave blank (use defaults)
5. Save

### Step 3: Test Charts
1. Add energy entries: 50, 40, 30 kWh
2. View charts - should show against 150 kWh weekly limit (600 monthly ÷ 4, adjusted for 2 members)
3. Add water entries: 3000, 2500, 2000 L
4. View charts - should show against 7500 L weekly limit

### Expected Result: ✅
- New accounts work with same logic
- Family member multiplier applied correctly (300 × 2 = 600)
- Charts show correct weekly limits
- No discrepancies compared to test accounts

---

## Verification Checklist

Print and mark off as you test:

- [ ] Cannot set custom limit > default limit (backend validation)
- [ ] Cannot set custom limit > default limit (frontend validation)
- [ ] Error messages clearly state the maximum allowed
- [ ] Charts show WEEKLY limit (monthly ÷ 4), not monthly
- [ ] Chart dates in MM-DD format
- [ ] Alert boxes show day-of-week (e.g., "Day 3 of 7")
- [ ] Alert boxes show weekly usage / weekly limit
- [ ] Alert boxes show both weekly AND monthly limits
- [ ] Cannot save entry that would exceed monthly limit
- [ ] Error shows remaining capacity in month
- [ ] Preview shows warning before saving
- [ ] Dashboard updates immediately after saving entry
- [ ] Alerts change color based on weekly usage percentage
- [ ] All test accounts behave identically
- [ ] New account works same as test accounts
- [ ] Family member multiplier works correctly

---

## Troubleshooting

### Charts Not Showing?
1. Open browser DevTools (F12)
2. Check Console for errors
3. Check Network tab - see if `/api/chart-data/<user_id>` returns data
4. Reload page and try again

### Limits Still Showing Wrong Values?
1. Clear browser cache (Ctrl+F5)
2. Check database was reset: `python init_database.py`
3. Verify backend code has fixes (check for "weekly_energy_limit = monthly_energy_limit / 4")

### Entry Not Saving?
1. Check the error message - is monthly limit being exceeded?
2. Check preview - does it show warning?
3. Check server logs - any errors?

### Test Account Behaves Differently?
1. Check if old data exists in database
2. Reset database: `python init_database.py`
3. Restart backend server
4. Clear browser cache and login again

---

## Success Criteria

### The Fix is Complete When:
✅ All 14 items in Verification Checklist are confirmed  
✅ No discrepancies between test accounts and new accounts  
✅ Charts display correctly for all user categories  
✅ Limit enforcement prevents exceeding monthly usage  
✅ Alerts accurately reflect resource status  
✅ Day-of-week information helps users plan consumption
