from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from database import db
from modules import User, EnergyEntry, WaterEntry, Notification
from config import Config
from datetime import datetime, timedelta
import json
import requests
import io
import csv

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
db.init_app(app)

# Serve Frontend Files
@app.route('/')
def serve_frontend():
    """Serve the main index.html file"""
    return send_from_directory('../FRONTEND', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (CSS, JS, images, etc.)"""
    return send_from_directory('../FRONTEND', path)

# Malawi Electricity Tariffs (ESCOM Rates)
ELECTRICITY_TARIFFS = {
    'single': {
        'first_50_kwh': 71.35,
        'above_50_kwh': 109.05,
        'monthly_fixed': 0,
        'default_energy_limit': 100,  # kWh per month
        'default_water_limit': 5000   # liters per month
    },
    'family': {
        'first_50_kwh': 71.35,
        'above_50_kwh': 109.05,
        'monthly_fixed': 8000,
        'default_energy_limit': 300,  # kWh per month for family
        'default_water_limit': 15000  # liters per month for family
    },
    'hostel': {
        'rate': 261.60,
        'monthly_fixed': 0,
        'default_energy_limit': 1000, # kWh per month for hostel
        'default_water_limit': 50000  # liters per month for hostel
    },
    'company': {
        'rate': 226.20,
        'monthly_fixed': 18130,
        'default_energy_limit': 5000, # kWh per month for company
        'default_water_limit': 100000 # liters per month for company
    }
}

# Default water prices (MWK per liter)
WATER_RATES = {
    'single': 2.5,
    'family': 2.5,
    'hostel': 3.0,
    'company': 3.5
}

with app.app_context():
    db.create_all()

# SMS Configuration (Simulated - replace with actual SMS service)
SMS_CONFIG = {
    'enabled': True,  # Set to False to disable SMS in development
    'api_key': 'your_sms_api_key',
    'api_secret': 'your_sms_api_secret',
    'sender_id': 'EnergyTrack'
}

def calculate_electricity_cost(user_category, usage, monthly_usage_so_far=0):
    """Calculate electricity cost based on user category and ESCOM tariffs"""
    tariff = ELECTRICITY_TARIFFS.get(user_category, ELECTRICITY_TARIFFS['single'])
    
    if user_category in ['single', 'family']:
        # Block tariff calculation
        remaining_first_block = max(0, 50 - monthly_usage_so_far)
        first_block_usage = min(usage, remaining_first_block)
        above_block_usage = max(0, usage - remaining_first_block)
        
        cost = (first_block_usage * tariff['first_50_kwh'] + 
                above_block_usage * tariff['above_50_kwh'] +
                tariff['monthly_fixed'])
    else:
        # Fixed rate for commercial categories
        cost = (usage * tariff['rate'] + tariff['monthly_fixed'])
    
    return round(cost, 2)

def calculate_water_cost(user_category, usage):
    """Calculate water cost based on user category"""
    rate = WATER_RATES.get(user_category, 2.5)
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
    tariff = ELECTRICITY_TARIFFS.get(user.user_category, ELECTRICITY_TARIFFS['single'])
    
    # Use custom limit if set, otherwise use default limit
    energy_limit = user.custom_energy_limit if user.custom_energy_limit > 0 else tariff['default_energy_limit']
    water_limit = user.custom_water_limit if user.custom_water_limit > 0 else tariff['default_water_limit']
    
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
    """Generate personalized conservation tips with criteria and category-specific guidance.

    Returns a list of structured tips: each tip is a dict with `title` and `detail`.
    """
    tips = []

    energy_limit, water_limit = get_user_limits(user)
    monthly_energy = get_monthly_usage(user.id, 'energy')
    monthly_water = get_monthly_usage(user.id, 'water')

    # Energy guidance
    if energy_limit > 0:
        energy_ratio = monthly_energy / energy_limit
    else:
        energy_ratio = 0

    if energy_ratio >= 1.0:
        tips.append({
            'title': 'Energy limit exceeded',
            'detail': f"Your monthly energy usage ({monthly_energy} kWh) has exceeded your limit ({energy_limit} kWh). Immediate actions: reduce HVAC/AC runtime, unplug idle appliances, and schedule high-consumption tasks (ironing, washing) during off-peak times." 
        })
    elif energy_ratio >= 0.8:
        tips.append({
            'title': 'Approaching energy limit',
            'detail': f"You're at {energy_ratio*100:.0f}% of your energy limit ({monthly_energy}/{energy_limit} kWh). Try dimming lights, using energy-efficient bulbs, and avoiding simultaneous heavy loads." 
        })
    elif energy_ratio >= 0.5:
        tips.append({
            'title': 'Moderate energy usage',
            'detail': f"Good job — you're using {monthly_energy} kWh this month. Continue small habits: unplug chargers, use fans instead of AC when possible, and maintain appliances for efficiency." 
        })
    else:
        tips.append({
            'title': 'Low energy usage',
            'detail': f"Excellent — your energy use ({monthly_energy} kWh) is well below the limit ({energy_limit} kWh). Keep monitoring to sustain efficiency." 
        })

    # Water guidance
    if water_limit > 0:
        water_ratio = monthly_water / water_limit
    else:
        water_ratio = 0

    if water_ratio >= 1.0:
        tips.append({
            'title': 'Water limit exceeded',
            'detail': f"Your monthly water usage ({monthly_water} L) exceeded the limit ({water_limit} L). Check for leaks, repair dripping taps, and avoid continuous outdoor watering." 
        })
    elif water_ratio >= 0.8:
        tips.append({
            'title': 'Approaching water limit',
            'detail': f"You're at {water_ratio*100:.0f}% of your water limit. Reduce shower time, reuse greywater where safe, and inspect toilets/taps for leaks." 
        })
    elif water_ratio >= 0.5:
        tips.append({
            'title': 'Moderate water usage',
            'detail': f"Nice — water usage ({monthly_water} L) is moderate. Continue good practices like fixing leaks and using efficient fixtures." 
        })
    else:
        tips.append({
            'title': 'Low water usage',
            'detail': f"Great — your water consumption ({monthly_water} L) is low compared to your limit ({water_limit} L). Share tips with others to spread conservation." 
        })

    # Category-specific suggestions
    category = user.user_category or 'single'
    if category == 'family':
        tips.append({
            'title': 'Family tips',
            'detail': 'For families, coordinate appliance use (stagger washing/drying), use energy-saving modes, and set household rules for shower times to reduce combined load.'
        })
    elif category in ['hostel', 'company']:
        tips.append({
            'title': 'Commercial tips',
            'detail': 'Consider bulk-efficiency measures: install timers, use LED lighting, schedule maintenance, and monitor meter readings to find abnormal spikes.'
        })
    else:
        tips.append({
            'title': 'General tips',
            'detail': 'Small changes compound: switch to LED bulbs, maintain appliances, insulate where possible, and fix leaks early.'
        })

    # Limit output size
    return tips[:6]

# Updated Registration Endpoint
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        user = User(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            phone_number=data.get('phone_number', ''),
            user_category=data.get('user_category', 'single'),
            family_members=data.get('family_members', 1),
            custom_energy_limit=data.get('custom_energy_limit', 0),
            custom_water_limit=data.get('custom_water_limit', 0)
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully', 
            'user_id': user.id,
            'username': user.username
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        user = User.query.filter_by(username=data.get('username')).first()
        if not user or user.password != data.get('password'):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        return jsonify({
            'message': 'Login successful',
            'user_id': user.id,
            'username': user.username
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Updated Energy Entry Endpoint
@app.route('/api/energy-entries', methods=['POST'])
def add_energy_entry():
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('electricity_usage') or not data.get('reading_date') or not data.get('user_id'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        try:
            electricity_usage = float(data['electricity_usage'])
            if electricity_usage <= 0:
                return jsonify({'error': 'Electricity usage must be greater than 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Electricity usage must be a valid number'}), 400
        
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Validate date
        try:
            reading_date = datetime.fromisoformat(data['reading_date'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if reading_date > datetime.now():
            return jsonify({'error': 'Reading date cannot be in the future'}), 400
            
        monthly_usage_so_far = get_monthly_usage(data['user_id'], 'energy')
        
        # Calculate cost automatically
        calculated_cost = calculate_electricity_cost(
            user.user_category, 
            data['electricity_usage'],
            monthly_usage_so_far
        )
        
        # Check if adding this entry would exceed monthly limit
        new_monthly_total = monthly_usage_so_far + data['electricity_usage']
        energy_limit, _ = get_user_limits(user)
        
        if new_monthly_total > energy_limit:
            return jsonify({
                'error': f'Adding this entry would exceed your monthly energy limit. You have {energy_limit - monthly_usage_so_far} kWh remaining.',
                'monthly_limit': energy_limit,
                'current_monthly_usage': monthly_usage_so_far,
                'requested_usage': data['electricity_usage'],
                'would_total': new_monthly_total
            }), 400
        
        entry = EnergyEntry(
            user_id=data['user_id'],
            electricity_usage=data['electricity_usage'],
            cost=calculated_cost,
            reading_date=datetime.fromisoformat(data['reading_date'])
        )
        
        db.session.add(entry)
        db.session.commit()
        
        # Check for high consumption
        check_high_consumption(user, data['electricity_usage'], 'energy')
        
        return jsonify({
            'message': 'Energy entry added successfully',
            'calculated_cost': calculated_cost,
            'monthly_usage_so_far': monthly_usage_so_far + data['electricity_usage']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Updated Water Entry Endpoint with Auto Cost Calculation
@app.route('/api/water-entries', methods=['POST'])
def add_water_entry():
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('water_usage') or not data.get('reading_date') or not data.get('user_id'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        try:
            water_usage = float(data['water_usage'])
            if water_usage <= 0:
                return jsonify({'error': 'Water usage must be greater than 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Water usage must be a valid number'}), 400
        
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Validate date
        try:
            reading_date = datetime.fromisoformat(data['reading_date'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if reading_date > datetime.now():
            return jsonify({'error': 'Reading date cannot be in the future'}), 400
        
        # Calculate cost automatically
        calculated_cost = calculate_water_cost(user.user_category, data['water_usage'])
        
        # Check if adding this entry would exceed monthly limit
        monthly_water_so_far = get_monthly_usage(data['user_id'], 'water')
        new_monthly_total = monthly_water_so_far + data['water_usage']
        _, water_limit = get_user_limits(user)
        
        if new_monthly_total > water_limit:
            return jsonify({
                'error': f'Adding this entry would exceed your monthly water limit. You have {water_limit - monthly_water_so_far} L remaining.',
                'monthly_limit': water_limit,
                'current_monthly_usage': monthly_water_so_far,
                'requested_usage': data['water_usage'],
                'would_total': new_monthly_total
            }), 400
        
        entry = WaterEntry(
            user_id=data['user_id'],
            water_usage=data['water_usage'],
            cost=calculated_cost,
            reading_date=reading_date
        )
        
        db.session.add(entry)
        db.session.commit()
        
        # Check for high consumption
        check_high_consumption(user, data['water_usage'], 'water')
        
        return jsonify({
            'message': 'Water entry added successfully',
            'calculated_cost': calculated_cost
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Preview endpoints: return calculated price and context without saving
@app.route('/api/preview/energy', methods=['POST'])
def preview_energy():
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('electricity_usage') or not data.get('user_id'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        try:
            electricity_usage = float(data['electricity_usage'])
            if electricity_usage <= 0:
                return jsonify({'error': 'Electricity usage must be greater than 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Electricity usage must be a valid number'}), 400
        
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        monthly_usage_so_far = get_monthly_usage(data['user_id'], 'energy')
        calculated_cost = calculate_electricity_cost(
            user.user_category,
            electricity_usage,
            monthly_usage_so_far
        )

        energy_limit, _ = get_user_limits(user)

        projected_monthly_total = monthly_usage_so_far + electricity_usage
        warning = None
        if projected_monthly_total > energy_limit:
            warning = f"Projected monthly energy usage ({projected_monthly_total} kWh) exceeds your limit ({energy_limit} kWh)."

        return jsonify({
            'calculated_cost': calculated_cost,
            'monthly_usage_so_far': monthly_usage_so_far,
            'projected_monthly_total': projected_monthly_total,
            'energy_limit': energy_limit,
            'warning': warning
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/preview/water', methods=['POST'])
def preview_water():
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('water_usage') or not data.get('user_id'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        try:
            water_usage = float(data['water_usage'])
            if water_usage <= 0:
                return jsonify({'error': 'Water usage must be greater than 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Water usage must be a valid number'}), 400
        
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        monthly_usage_so_far = get_monthly_usage(data['user_id'], 'water')
        calculated_cost = calculate_water_cost(user.user_category, water_usage)

        _, water_limit = get_user_limits(user)
        projected_monthly_total = monthly_usage_so_far + water_usage
        warning = None
        if projected_monthly_total > water_limit:
            warning = f"Projected monthly water usage ({projected_monthly_total} L) exceeds your limit ({water_limit} L)."

        return jsonify({
            'calculated_cost': calculated_cost,
            'monthly_usage_so_far': monthly_usage_so_far,
            'projected_monthly_total': projected_monthly_total,
            'water_limit': water_limit,
            'warning': warning
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

# Chart Data Endpoint - Returns data formatted for line charts showing week-by-week limits and consumption
@app.route('/api/chart-data/<int:user_id>', methods=['GET'])
def get_chart_data(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get last 7 days of data (inclusive of today)
        now = datetime.now()
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        start_date = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        
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
        
        # Get user limits (monthly)
        monthly_energy_limit, monthly_water_limit = get_user_limits(user)
        # Convert to weekly limits (1/4 of monthly for 7-day week)
        weekly_energy_limit = monthly_energy_limit / 4
        weekly_water_limit = monthly_water_limit / 4
        
        # Build cumulative data arrays for the 7 days
        dates = []
        energy_data = []
        water_data = []
        cumulative_energy = 0
        cumulative_water = 0
        
        # Create 7-day timeline
        for i in range(7):
            current_day = start_date + timedelta(days=i)
            date_str = current_day.strftime('%m-%d')
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
        
        # Days used in the 7-day week (how many days have passed since start_date)
        days_elapsed = (end_date.date() - start_date.date()).days
        days_remaining_in_week = 7 - days_elapsed
        
        # Calculate days until limit exceeded
        energy_days_until_limit = (weekly_energy_limit - cumulative_energy) / avg_daily_energy if avg_daily_energy > 0 else float('inf')
        water_days_until_limit = (weekly_water_limit - cumulative_water) / avg_daily_water if avg_daily_water > 0 else float('inf')
        
        # Calculate end dates based on the weekly limit
        energy_limit_date = (end_date + timedelta(days=energy_days_until_limit)).strftime('%Y-%m-%d') if energy_days_until_limit != float('inf') else 'Not expected'
        water_limit_date = (end_date + timedelta(days=water_days_until_limit)).strftime('%Y-%m-%d') if water_days_until_limit != float('inf') else 'Not expected'
        
        # Weekly summary
        weekly_summary = [{
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'energy_total': cumulative_energy,
            'water_total': cumulative_water,
            'energy_status': 'OVER' if cumulative_energy > weekly_energy_limit else 'UNDER',
            'water_status': 'OVER' if cumulative_water > weekly_water_limit else 'UNDER',
            'days_elapsed': days_elapsed,
            'days_remaining': days_remaining_in_week
        }]
        
        return jsonify({
            'dates': dates,
            'energy_data': energy_data,
            'water_data': water_data,
            'energy_limit': weekly_energy_limit,
            'water_limit': weekly_water_limit,
            'monthly_energy_limit': monthly_energy_limit,
            'monthly_water_limit': monthly_water_limit,
            'energy_end_date': energy_limit_date,
            'water_end_date': water_limit_date,
            'days_remaining_energy': round(energy_days_until_limit, 1) if energy_days_until_limit != float('inf') else 'Unlimited',
            'days_remaining_water': round(water_days_until_limit, 1) if water_days_until_limit != float('inf') else 'Unlimited',
            'days_elapsed': days_elapsed,
            'days_remaining_in_week': days_remaining_in_week,
            'weekly_summary': weekly_summary,
            'resource_exhaustion': {
                'energy': {
                    'projected_end_date': energy_limit_date,
                    'days_remaining': round(energy_days_until_limit, 1) if energy_days_until_limit != float('inf') else 'Unlimited',
                    'current_usage': cumulative_energy,
                    'weekly_limit': weekly_energy_limit,
                    'monthly_limit': monthly_energy_limit,
                    'status': 'EXCEEDED' if cumulative_energy > weekly_energy_limit else ('WARNING' if cumulative_energy > weekly_energy_limit * 0.8 else 'GOOD')
                },
                'water': {
                    'projected_end_date': water_limit_date,
                    'days_remaining': round(water_days_until_limit, 1) if water_days_until_limit != float('inf') else 'Unlimited',
                    'current_usage': cumulative_water,
                    'weekly_limit': weekly_water_limit,
                    'monthly_limit': monthly_water_limit,
                    'status': 'EXCEEDED' if cumulative_water > weekly_water_limit else ('WARNING' if cumulative_water > weekly_water_limit * 0.8 else 'GOOD')
                }
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Updated Analytics Endpoint
@app.route('/api/analytics/<int:user_id>', methods=['GET'])
def get_analytics(user_id):
    try:
        # Accept optional start_date and end_date (YYYY-MM-DD). Default to last 30 days.
        start_str = request.args.get('start_date')
        end_str = request.args.get('end_date')

        if start_str and end_str:
            start_date = datetime.fromisoformat(start_str)
            end_date = datetime.fromisoformat(end_str) + timedelta(days=1)  # inclusive
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

        # Query entries within range
        energy_entries = EnergyEntry.query.filter(
            EnergyEntry.user_id == user_id,
            EnergyEntry.reading_date >= start_date,
            EnergyEntry.reading_date < end_date
        ).order_by(EnergyEntry.reading_date).all()

        water_entries = WaterEntry.query.filter(
            WaterEntry.user_id == user_id,
            WaterEntry.reading_date >= start_date,
            WaterEntry.reading_date < end_date
        ).order_by(WaterEntry.reading_date).all()

        total_energy = sum(entry.electricity_usage for entry in energy_entries)
        total_water = sum(entry.water_usage for entry in water_entries)
        total_cost = sum(entry.cost for entry in energy_entries) + sum(entry.cost for entry in water_entries)

        user = User.query.get(user_id)
        monthly_energy = get_monthly_usage(user_id, 'energy')
        monthly_water = get_monthly_usage(user_id, 'water')
        energy_limit, water_limit = get_user_limits(user)

        # Build series data (by entry) and simple daily aggregation
        series = []
        for entry in energy_entries:
            series.append({'date': entry.reading_date.strftime('%Y-%m-%d'), 'usage': entry.electricity_usage, 'cost': entry.cost, 'type': 'energy'})
        for entry in water_entries:
            series.append({'date': entry.reading_date.strftime('%Y-%m-%d'), 'usage': entry.water_usage, 'cost': entry.cost, 'type': 'water'})

        series = sorted(series, key=lambda x: x['date'])

        # Last update timestamp
        last_update = None
        all_entries = sorted(energy_entries + water_entries, key=lambda x: x.reading_date) if (energy_entries or water_entries) else []
        if all_entries:
            last_update = all_entries[-1].reading_date.isoformat()

        # Previous period comparison (same length immediately before start_date)
        period_days = (end_date - start_date).days
        prev_end = start_date
        prev_start = start_date - timedelta(days=period_days)

        prev_energy_entries = EnergyEntry.query.filter(
            EnergyEntry.user_id == user_id,
            EnergyEntry.reading_date >= prev_start,
            EnergyEntry.reading_date < prev_end
        ).all()

        prev_water_entries = WaterEntry.query.filter(
            WaterEntry.user_id == user_id,
            WaterEntry.reading_date >= prev_start,
            WaterEntry.reading_date < prev_end
        ).all()

        prev_total_energy = sum(e.electricity_usage for e in prev_energy_entries)
        prev_total_water = sum(w.water_usage for w in prev_water_entries)

        tips = generate_conservation_tips(energy_entries, water_entries, user)

        # Percentages for current period vs limits
        energy_percentage = min(100, (monthly_energy / energy_limit) * 100) if energy_limit > 0 else 0
        water_percentage = min(100, (monthly_water / water_limit) * 100) if water_limit > 0 else 0

        return jsonify({
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': (end_date - timedelta(days=1)).strftime('%Y-%m-%d'),
            'last_update': last_update,
            'total_energy': total_energy,
            'total_water': total_water,
            'total_cost': total_cost,
            'energy_trend': calculate_trend(energy_entries, 'electricity_usage'),
            'water_trend': calculate_trend(water_entries, 'water_usage'),
            'conservation_tips': tips,
            'series': series,
            'user_category': user.user_category,
            'energy_limit': energy_limit,
            'water_limit': water_limit,
            'monthly_energy_used': monthly_energy,
            'monthly_water_used': monthly_water,
            'energy_percentage': energy_percentage,
            'water_percentage': water_percentage,
            'previous_period': {
                'start_date': prev_start.strftime('%Y-%m-%d'),
                'end_date': (prev_end - timedelta(days=1)).strftime('%Y-%m-%d'),
                'total_energy': prev_total_energy,
                'total_water': prev_total_water
            },
            'has_custom_energy_limit': user.custom_energy_limit > 0,
            'has_custom_water_limit': user.custom_water_limit > 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/report/<int:user_id>', methods=['GET'])
def generate_report(user_id):
    try:
        # Accept optional start_date and end_date
        start_str = request.args.get('start_date')
        end_str = request.args.get('end_date')
        fmt = request.args.get('format', 'csv').lower()

        if start_str and end_str:
            start_date = datetime.fromisoformat(start_str)
            end_date = datetime.fromisoformat(end_str) + timedelta(days=1)
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

        energy_entries = EnergyEntry.query.filter(
            EnergyEntry.user_id == user_id,
            EnergyEntry.reading_date >= start_date,
            EnergyEntry.reading_date < end_date
        ).order_by(EnergyEntry.reading_date).all()

        water_entries = WaterEntry.query.filter(
            WaterEntry.user_id == user_id,
            WaterEntry.reading_date >= start_date,
            WaterEntry.reading_date < end_date
        ).order_by(WaterEntry.reading_date).all()

        # Build simple rows
        rows = []
        for e in energy_entries:
            rows.append({'type':'energy','date': e.reading_date.strftime('%Y-%m-%d'), 'usage': e.electricity_usage, 'cost': e.cost})
        for w in water_entries:
            rows.append({'type':'water','date': w.reading_date.strftime('%Y-%m-%d'), 'usage': w.water_usage, 'cost': w.cost})

        rows = sorted(rows, key=lambda x: x['date'])

        if fmt == 'json':
            return jsonify({'report': rows, 'start_date': start_date.strftime('%Y-%m-%d'), 'end_date': (end_date - timedelta(days=1)).strftime('%Y-%m-%d')})

        # default csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['type','date','usage','cost'])
        for r in rows:
            writer.writerow([r['type'], r['date'], r['usage'], r['cost']])

        csv_data = output.getvalue()
        return Response(csv_data, mimetype='text/csv', headers={
            'Content-Disposition': f'attachment; filename=report_{user_id}_{start_date.strftime("%Y%m%d")}_{(end_date - timedelta(days=1)).strftime("%Y%m%d")}.csv'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Updated User Categories Endpoint
@app.route('/api/user-categories', methods=['GET'])
def get_user_categories():
    categories = []
    for cat_id, details in ELECTRICITY_TARIFFS.items():
        categories.append({
            'id': cat_id,
            'name': cat_id.capitalize() + ' User',
            'description': f"{details['default_energy_limit']} kWh energy, {details['default_water_limit']} L water default limits",
            'tariff_details': details,
            'default_energy_limit': details['default_energy_limit'],
            'default_water_limit': details['default_water_limit']
        })
    
    return jsonify({
        'categories': categories,
        'tariffs': ELECTRICITY_TARIFFS,
        'water_rates': WATER_RATES
    })

# Updated Profile Update Endpoint
@app.route('/api/user/<int:user_id>/profile', methods=['PUT'])
def update_user_profile(user_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Validate and update fields
        try:
            if 'user_category' in data:
                valid_categories = ['single', 'family', 'hostel', 'company']
                if data['user_category'].lower() not in valid_categories:
                    return jsonify({'error': 'Invalid category'}), 400
                user.user_category = data['user_category'].lower()
            
            if 'family_members' in data:
                fam_members = int(data['family_members'])
                if fam_members < 1:
                    return jsonify({'error': 'Family members must be at least 1'}), 400
                user.family_members = fam_members
            
            if 'phone_number' in data:
                user.phone_number = data['phone_number']
            
            if 'custom_energy_limit' in data:
                if data['custom_energy_limit']:
                    limit = float(data['custom_energy_limit'])
                    if limit < 0:
                        return jsonify({'error': 'Custom energy limit cannot be negative'}), 400
                    tariff = ELECTRICITY_TARIFFS.get(user.user_category, ELECTRICITY_TARIFFS['single'])
                    default_limit = tariff['default_energy_limit']
                    if limit > default_limit:
                        return jsonify({'error': f'Custom energy limit cannot exceed default limit of {default_limit} kWh'}), 400
                    user.custom_energy_limit = limit
                else:
                    user.custom_energy_limit = 0
            
            if 'custom_water_limit' in data:
                if data['custom_water_limit']:
                    limit = float(data['custom_water_limit'])
                    if limit < 0:
                        return jsonify({'error': 'Custom water limit cannot be negative'}), 400
                    tariff = ELECTRICITY_TARIFFS.get(user.user_category, ELECTRICITY_TARIFFS['single'])
                    default_limit = tariff['default_water_limit']
                    if limit > default_limit:
                        return jsonify({'error': f'Custom water limit cannot exceed default limit of {default_limit} liters'}), 400
                    user.custom_water_limit = limit
                else:
                    user.custom_water_limit = 0
        
        except (ValueError, TypeError) as ve:
            return jsonify({'error': f'Invalid data format: {str(ve)}'}), 400
        
        db.session.commit()
        
        # Get updated limits for response
        energy_limit, water_limit = get_user_limits(user)
        
        return jsonify({
            'message': 'Profile updated successfully',
            'energy_limit': energy_limit,
            'water_limit': water_limit,
            'has_custom_energy_limit': user.custom_energy_limit > 0,
            'has_custom_water_limit': user.custom_water_limit > 0
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# New Endpoint: Get default limits for a category
@app.route('/api/category-defaults/<category>', methods=['GET'])
def get_category_defaults(category):
    tariff = ELECTRICITY_TARIFFS.get(category, ELECTRICITY_TARIFFS['single'])
    return jsonify({
        'default_energy_limit': tariff['default_energy_limit'],
        'default_water_limit': tariff['default_water_limit']
    })

# Rest of the endpoints remain the same...
@app.route('/api/energy-entries/<int:user_id>', methods=['GET'])
def get_energy_entries(user_id):
    entries = EnergyEntry.query.filter_by(user_id=user_id).order_by(EnergyEntry.reading_date.desc()).all()
    return jsonify([entry.to_dict() for entry in entries])

@app.route('/api/water-entries/<int:user_id>', methods=['GET'])
def get_water_entries(user_id):
    entries = WaterEntry.query.filter_by(user_id=user_id).order_by(WaterEntry.reading_date.desc()).all()
    return jsonify([entry.to_dict() for entry in entries])

@app.route('/api/notifications/<int:user_id>', methods=['GET'])
def get_notifications(user_id):
    notifications = Notification.query.filter_by(user_id=user_id, is_read=False).order_by(Notification.created_at.desc()).all()
    return jsonify([{
        'id': n.id,
        'message': n.message,
        'type': n.type,
        'sms_sent': n.sms_sent,
        'created_at': n.created_at.isoformat()
    } for n in notifications])

@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_read(notification_id):
    notification = Notification.query.get(notification_id)
    if notification:
        notification.is_read = True
        db.session.commit()
        return jsonify({'message': 'Notification marked as read'})
    return jsonify({'error': 'Notification not found'}), 404

@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    user = User.query.get(user_id)
    if user:
        energy_limit, water_limit = get_user_limits(user)
        return jsonify({
            'username': user.username,
            'email': user.email,
            'phone_number': user.phone_number,
            'user_category': user.user_category,
            'family_members': user.family_members,
            'custom_energy_limit': user.custom_energy_limit,
            'custom_water_limit': user.custom_water_limit,
            'effective_energy_limit': energy_limit,
            'effective_water_limit': water_limit,
            'created_at': user.created_at.isoformat()
        })
    return jsonify({'error': 'User not found'}), 404

def calculate_trend(entries, field):
    if len(entries) < 2:
        return 'stable'
    
    sorted_entries = sorted(entries, key=lambda x: x.reading_date)
    recent = getattr(sorted_entries[-1], field)
    previous = getattr(sorted_entries[0], field)
    
    if recent > previous * 1.1:
        return 'increasing'
    elif recent < previous * 0.9:
        return 'decreasing'
    else:
        return 'stable'

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy', 
        'message': 'Smart Energy Tracker API v2.1 is running',
        'timestamp': datetime.now().isoformat(),
        'features': ['User Categories', 'Custom Limits', 'ESCOM Tariffs', 'SMS Alerts', 'Data Visualization']
    })

if __name__ == '__main__':
    print("Starting Smart Energy Tracker API v2.1...")
    print("URL: http://localhost:5000")
    print("Features: User Categories, Custom Limits, Automatic Cost Calculation, SMS Notifications, Charts")
    print("Using Malawi ESCOM Electricity Tariffs")
    app.run(debug=True, port=5000)