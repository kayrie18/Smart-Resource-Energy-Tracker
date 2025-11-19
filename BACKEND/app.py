from flask import Flask, request, jsonify, Response
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
        message = f"ALERT {user.username}: Monthly {resource_name} usage ({monthly_usage}{unit}) exceeded your limit ({limit}{unit})."
        
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
        
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        monthly_usage_so_far = get_monthly_usage(data['user_id'], 'energy')
        
        # Calculate cost automatically
        calculated_cost = calculate_electricity_cost(
            user.user_category, 
            data['electricity_usage'],
            monthly_usage_so_far
        )
        
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
        
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Calculate cost automatically
        calculated_cost = calculate_water_cost(user.user_category, data['water_usage'])
        
        entry = WaterEntry(
            user_id=data['user_id'],
            water_usage=data['water_usage'],
            cost=calculated_cost,
            reading_date=datetime.fromisoformat(data['reading_date'])
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
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        monthly_usage_so_far = get_monthly_usage(data['user_id'], 'energy')
        calculated_cost = calculate_electricity_cost(
            user.user_category,
            data['electricity_usage'],
            monthly_usage_so_far
        )

        energy_limit, _ = get_user_limits(user)

        projected_monthly_total = monthly_usage_so_far + data['electricity_usage']
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
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        monthly_usage_so_far = get_monthly_usage(data['user_id'], 'water')
        calculated_cost = calculate_water_cost(user.user_category, data['water_usage'])

        _, water_limit = get_user_limits(user)
        projected_monthly_total = monthly_usage_so_far + data['water_usage']
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
    data = request.get_json()
    user = User.query.get(user_id)
    
    if user:
        if 'user_category' in data:
            user.user_category = data['user_category']
        if 'family_members' in data:
            user.family_members = data['family_members']
        if 'phone_number' in data:
            user.phone_number = data['phone_number']
        if 'custom_energy_limit' in data:
            user.custom_energy_limit = float(data['custom_energy_limit'])
        if 'custom_water_limit' in data:
            user.custom_water_limit = float(data['custom_water_limit'])
        
        db.session.commit()
        
        # Get updated limits for response
        energy_limit, water_limit = get_user_limits(user)
        
        return jsonify({
            'message': 'Profile updated successfully',
            'energy_limit': energy_limit,
            'water_limit': water_limit,
            'has_custom_energy_limit': user.custom_energy_limit > 0,
            'has_custom_water_limit': user.custom_water_limit > 0
        })
    
    return jsonify({'error': 'User not found'}), 404

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
    print("🚀 Starting Smart Energy Tracker API v2.1...")
    print("📍 http://localhost:5000")
    print("📊 Features: User Categories, Custom Limits, Automatic Cost Calculation, SMS Notifications, Charts")
    print("🇲🇼 Using Malawi ESCOM Electricity Tariffs")
    app.run(debug=True, port=5000)