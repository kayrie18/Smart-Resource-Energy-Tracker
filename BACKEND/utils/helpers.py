from datetime import datetime
from modules import User, EnergyEntry, WaterEntry, Notification
from database import db

# Default/Fallback Malawi Electricity Tariffs (ESCOM Rates - Verified Feb 2025)
DEFAULT_ELECTRICITY_TARIFFS = {
    'single': {'first_50_kwh': 71.35, 'above_50_kwh': 109.05, 'monthly_fixed': 0, 'default_energy_limit': 100, 'default_water_limit': 5000},
    'family': {'first_50_kwh': 71.35, 'above_50_kwh': 109.05, 'monthly_fixed': 8000, 'default_energy_limit': 300, 'default_water_limit': 15000},
    'hostel': {'rate': 261.60, 'monthly_fixed': 0, 'default_energy_limit': 1000, 'default_water_limit': 50000},
    'company': {'rate': 226.20, 'monthly_fixed': 18130, 'default_energy_limit': 5000, 'default_water_limit': 100000}
}
DEFAULT_WATER_RATES = {'single': 3.20, 'family': 3.20, 'hostel': 5.50, 'company': 8.00}

SMS_CONFIG = {
    'enabled': True, 
    'api_key': 'your_sms_api_key', 
    'api_secret': 'your_sms_api_secret', 
    'sender_id': 'EnergyTrack'
}

def get_db_tariff(resource_type, user_category):
    """Fetch tariff from DB or return None to use fallback"""
    from modules import Tariff
    try:
        tariff = Tariff.query.filter_by(resource_type=resource_type, user_category=user_category).first()
        return tariff
    except:
        return None

def calculate_electricity_cost(user_category, usage, monthly_usage_so_far=0):
    """Calculate electricity cost based on DB tariffs or Fallback"""
    db_tariff = get_db_tariff('energy', user_category)
    
    if db_tariff:
        # Use Database Tariff
        if user_category in ['single', 'family']:
            remaining_first_block = max(0, db_tariff.tier_1_limit - monthly_usage_so_far)
            first_block_usage = min(usage, remaining_first_block)
            above_block_usage = max(0, usage - remaining_first_block)
            cost = (first_block_usage * db_tariff.tier_1_rate + 
                    above_block_usage * db_tariff.tier_2_rate + 
                    db_tariff.fixed_charge)
        else:
            cost = (usage * db_tariff.rate_per_unit + db_tariff.fixed_charge)
    else:
        # Use Fallback
        tariff = DEFAULT_ELECTRICITY_TARIFFS.get(user_category, DEFAULT_ELECTRICITY_TARIFFS['single'])
        if user_category in ['single', 'family']:
            remaining_first_block = max(0, 50 - monthly_usage_so_far)
            first_block_usage = min(usage, remaining_first_block)
            above_block_usage = max(0, usage - remaining_first_block)
            cost = (first_block_usage * tariff['first_50_kwh'] + 
                    above_block_usage * tariff['above_50_kwh'] +
                    tariff['monthly_fixed'])
        else:
            cost = (usage * tariff['rate'] + tariff['monthly_fixed'])
            
    return round(cost, 2)

def calculate_water_cost(user_category, usage):
    """Calculate water cost based on DB or Fallback"""
    db_tariff = get_db_tariff('water', user_category)
    if db_tariff:
        rate = db_tariff.rate_per_unit
    else:
        rate = DEFAULT_WATER_RATES.get(user_category, 2.5)
    return round(usage * rate, 2)

def get_monthly_usage(user_id, resource_type='energy'):
    """Get current month's total usage for a user"""
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    if resource_type == 'energy':
        monthly_entries = EnergyEntry.query.filter(
            EnergyEntry.user_id == user_id,
            EnergyEntry.reading_date >= start_of_month
        ).all()
        return sum(entry.electricity_usage for entry in monthly_entries)
    else:  # water
        monthly_entries = WaterEntry.query.filter(
            WaterEntry.user_id == user_id,
            WaterEntry.reading_date >= start_of_month
        ).all()
        return sum(entry.water_usage for entry in monthly_entries)

def get_user_limits(user):
    """Get the effective limits for a user (custom or default)"""
def get_user_limits(user):
    """Get the effective limits for a user (custom or default)"""
    # Try DB, then fallback
    db_tariff_energy = get_db_tariff('energy', user.user_category)
    db_tariff_water = get_db_tariff('water', user.user_category)
    
    default_energy = db_tariff_energy.default_limit if db_tariff_energy else DEFAULT_ELECTRICITY_TARIFFS.get(user.user_category, DEFAULT_ELECTRICITY_TARIFFS['single'])['default_energy_limit']
    default_water = db_tariff_water.default_limit if db_tariff_water else DEFAULT_ELECTRICITY_TARIFFS.get(user.user_category, DEFAULT_ELECTRICITY_TARIFFS['single'])['default_water_limit']
    
    # Use custom limit if set, otherwise use default limit
    energy_limit = user.custom_energy_limit if user.custom_energy_limit > 0 else default_energy
    water_limit = user.custom_water_limit if user.custom_water_limit > 0 else default_water
    
    # Adjust limits for family based on members
    if user.user_category == 'family' and user.family_members > 1:
        energy_limit = energy_limit * user.family_members
        water_limit = water_limit * user.family_members
    
    return energy_limit, water_limit

def send_sms_notification(phone_number, message):
    """Send SMS notification"""
    if not SMS_CONFIG['enabled'] or not phone_number:
        print(f"SMS simulation: {message}")
        return True
        
    try:
        # Example integration with actual SMS service
        # response = requests.post(
        #     'https://api.sms-service.com/send',
        #     data={
        #         'api_key': SMS_CONFIG['api_key'],
        #         'api_secret': SMS_CONFIG['api_secret'],
        #         'to': phone_number,
        #         'from': SMS_CONFIG['sender_id'],
        #         'message': message
        #     }
        # )
        print(f"📱 SMS sent to {phone_number}: {message}")
        return True
    except Exception as e:
        print(f"❌ SMS sending failed: {str(e)}")
        return False

def check_high_consumption(user, usage, resource_type='energy'):
    """Check for high consumption and send notifications"""
    monthly_usage = get_monthly_usage(user.id, resource_type)
    energy_limit, water_limit = get_user_limits(user)
    
    if resource_type == 'energy':
        limit = energy_limit
        resource_name = "energy"
        unit = "kWh"
    else:
        limit = water_limit
        resource_name = "water"
        unit = "liters"
    
    if monthly_usage > limit:
        message = f"ALERT {user.username}: Monthly {resource_name} usage ({monthly_usage} {unit}) exceeded your limit ({limit} {unit})."
        
        # Create notification
        notification = Notification(
            user_id=user.id,
            message=message,
            type='warning'
        )
        db.session.add(notification)
        
        # Send SMS if phone number exists
        if user.phone_number:
            notification.sms_sent = send_sms_notification(user.phone_number, message)
        
        db.session.commit()

def generate_conservation_tips(energy_entries, water_entries, user):
    """Generate personalized conservation tips based on usage"""
    tips = []
    
    # --- Energy Tips ---
    has_energy_alert = False
    
    # 1. Check Spikes
    if energy_entries:
        last_energy = energy_entries[-1]
        if last_energy.electricity_usage > 15: 
            tips.append({
                'title': '[Energy] High Recent Usage',
                'detail': f"Last reading: {last_energy.electricity_usage} kWh. Check for appliances left on."
            })
            has_energy_alert = True
            
    # 2. Check Averages
    avg_energy = sum(e.electricity_usage for e in energy_entries) / len(energy_entries) if energy_entries else 0
    if avg_energy > 10: 
        tips.append({
            'title': '[Energy] High Daily Average',
            'detail': 'Consider switching to LED bulbs and managing AC usage to lower your daily average.'
        })
        has_energy_alert = True
    
    # 3. Always show distinct Energy Tip if no critical alerts
    if not has_energy_alert:
        tips.append({
            'title': '[Energy] Efficient Habits',
            'detail': 'Great job keeping usage low! Remember to unplug electronics to avoid phantom load.'
        })


    # --- Water Tips ---
    has_water_alert = False
    
    # 1. Check Spikes
    if water_entries:
        last_water = water_entries[-1]
        if last_water.water_usage > 400:
            tips.append({
                'title': '[Water] High Recent Usage',
                'detail': f"Last reading: {last_water.water_usage} L. Check for visible leaks around the house."
            })
            has_water_alert = True

    # 2. Check Averages
    avg_water = sum(w.water_usage for w in water_entries) / len(water_entries) if water_entries else 0
    if avg_water > 300: 
        tips.append({
            'title': '[Water] High Daily Average',
            'detail': 'Shorten showers by 2 minutes to save up to 40 liters per day.'
        })
        has_water_alert = True
        
    # 3. Always show distinct Water Tip if no critical alerts
    if not has_water_alert:
         tips.append({
            'title': '[Water] Conservation Pro',
            'detail': 'Your water usage is efficient. Check taps occasionally to ensure no new leaks form.'
        })
        
    # --- General / Encouragement ---
    # Only add if total tips are few
    if len(tips) < 3:
        tips.append({
            'title': '[General] Sustainable Living',
            'detail': 'Small changes add up! You are making a difference for the planet.'
        })
        
    return tips
