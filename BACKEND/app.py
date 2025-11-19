from flask import Flask, request, jsonify
from flask_cors import CORS
from database import db
from models import User, EnergyEntry, WaterEntry, Notification
from config import Config
from datetime import datetime, timedelta
import json
import requests

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
    """Generate personalized conservation tips"""
    tips = []
    
    energy_limit, water_limit = get_user_limits(user)
    monthly_energy = get_monthly_usage(user.id, 'energy')
    monthly_water = get_monthly_usage(user.id, 'water')
    
    # Energy tips based on usage vs limit
    if monthly_energy > energy_limit * 0.8:  # 80% of limit
        tips.append("🚨 You're approaching your energy limit! Consider reducing usage.")
    elif monthly_energy > energy_limit * 0.5:  # 50% of limit
        tips.append("💡 Moderate energy usage. Good job staying within your limits.")
    else:
        tips.append("✅ Excellent! Your energy consumption is well within your limits.")
    
    # Water tips based on usage vs limit
    if monthly_water > water_limit * 0.8:
        tips.append("💧 You're approaching your water limit! Check for leaks and reduce usage.")
    elif monthly_water > water_limit * 0.5:
        tips.append("💧 Moderate water usage. You're managing your water well.")
    else:
        tips.append("💧 Great! Your water usage is well within your limits.")
    
    # General tips
    tips.extend([
        "🔌 Unplug chargers and appliances when not in use",
        "🚿 Take shorter showers to save water and energy",
        "🌞 Use natural ventilation instead of AC when possible"
    ])
    
    return tips[:5]  # Return max 5 tips

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

# Updated Analytics Endpoint
@app.route('/api/analytics/<int:user_id>', methods=['GET'])
def get_analytics(user_id):
    try:
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # Energy analytics
        energy_entries = EnergyEntry.query.filter(
            EnergyEntry.user_id == user_id,
            EnergyEntry.reading_date >= thirty_days_ago
        ).order_by(EnergyEntry.reading_date).all()
        
        # Water analytics
        water_entries = WaterEntry.query.filter(
            WaterEntry.user_id == user_id,
            WaterEntry.reading_date >= thirty_days_ago
        ).all()
        
        total_energy = sum(entry.electricity_usage for entry in energy_entries)
        total_water = sum(entry.water_usage for entry in water_entries)
        total_cost = sum(entry.cost for entry in energy_entries) + sum(entry.cost for entry in water_entries)
        
        user = User.query.get(user_id)
        monthly_energy = get_monthly_usage(user_id, 'energy')
        monthly_water = get_monthly_usage(user_id, 'water')
        energy_limit, water_limit = get_user_limits(user)
        
        # Chart data
        chart_data = {
            'energy_usage': [
                {'date': entry.reading_date.strftime('%Y-%m-%d'), 'usage': entry.electricity_usage}
                for entry in energy_entries[-7:]  # Last 7 days for chart
            ],
            'cost_trend': [
                {'date': entry.reading_date.strftime('%Y-%m-%d'), 'cost': entry.cost}
                for entry in energy_entries[-7:]
            ],
            'monthly_breakdown': {
                'energy_usage': total_energy,
                'water_usage': total_water,
                'total_cost': total_cost,
                'energy_limit': energy_limit,
                'water_limit': water_limit,
                'monthly_energy_used': monthly_energy,
                'monthly_water_used': monthly_water
            }
        }
        
        tips = generate_conservation_tips(energy_entries, water_entries, user)
        
        # Calculate percentages
        energy_percentage = min(100, (monthly_energy / energy_limit) * 100) if energy_limit > 0 else 0
        water_percentage = min(100, (monthly_water / water_limit) * 100) if water_limit > 0 else 0
        
        return jsonify({
            'total_energy': total_energy,
            'total_water': total_water,
            'total_cost': total_cost,
            'energy_trend': calculate_trend(energy_entries, 'electricity_usage'),
            'water_trend': calculate_trend(water_entries, 'water_usage'),
            'conservation_tips': tips,
            'chart_data': chart_data,
            'user_category': user.user_category,
            'energy_limit': energy_limit,
            'water_limit': water_limit,
            'monthly_energy_used': monthly_energy,
            'monthly_water_used': monthly_water,
            'energy_percentage': energy_percentage,
            'water_percentage': water_percentage,
            'has_custom_energy_limit': user.custom_energy_limit > 0,
            'has_custom_water_limit': user.custom_water_limit > 0
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