from flask import Blueprint, request, jsonify
from modules import User
from database import db
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
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
            password=generate_password_hash(data['password']),
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

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        print(f"Login attempt for: {data.get('username')}")
        
        user = User.query.filter_by(username=data.get('username')).first()
        
        if not user:
            print("User not found")
            return jsonify({'error': 'Invalid username or password'}), 401
            
        is_valid = check_password_hash(user.password, data.get('password'))
        print(f"Password check result: {is_valid}")
        
        if not is_valid:
            print(f"Hash in DB: {user.password}")
            print(f"Password provided: {data.get('password')}")
            return jsonify({'error': 'Invalid username or password'}), 401
        
        return jsonify({
            'message': 'Login successful',
            'user_id': user.id,
            'username': user.username,
            'is_admin': user.is_admin
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        from utils.helpers import get_user_limits
        energy_limit, water_limit = get_user_limits(user)
        
        return jsonify({
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'phone_number': user.phone_number,
            'user_category': user.user_category,
            'family_members': user.family_members,
            'custom_energy_limit': user.custom_energy_limit,
            'custom_water_limit': user.custom_water_limit,
            'effective_energy_limit': energy_limit,
            'effective_water_limit': water_limit
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/user/<int:user_id>/profile', methods=['PUT'])
def update_user_profile(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        data = request.get_json()
        
        if 'custom_energy_limit' in data:
            user.custom_energy_limit = float(data['custom_energy_limit'])
        if 'custom_water_limit' in data:
            user.custom_water_limit = float(data['custom_water_limit'])
            
        db.session.commit()
        
        return jsonify({'message': 'Profile updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/user-categories', methods=['GET'])
def get_user_categories():
    return jsonify({
        'categories': [
            {'id': 'single', 'name': 'Single User'},
            {'id': 'family', 'name': 'Family'},
            {'id': 'hostel', 'name': 'Hostel'},
            {'id': 'company', 'name': 'Company'}
        ]
    })

@auth_bp.route('/admin/tariff', methods=['PUT'])
def update_tariff():
    try:
        data = request.get_json()
        resource_type = data.get('resource_type')
        user_category = data.get('user_category')
        
        from modules import Tariff
        from database import db
        
        tariff = Tariff.query.filter_by(resource_type=resource_type, user_category=user_category).first()
        if not tariff:
            return jsonify({'error': 'Tariff not found'}), 404
            
        # Update fields dynamically
        if 'rate_per_unit' in data: tariff.rate_per_unit = float(data['rate_per_unit'])
        if 'fixed_charge' in data: tariff.fixed_charge = float(data['fixed_charge'])
        if 'tier_1_limit' in data: tariff.tier_1_limit = float(data['tier_1_limit'])
        if 'tier_1_rate' in data: tariff.tier_1_rate = float(data['tier_1_rate'])
        if 'tier_2_rate' in data: tariff.tier_2_rate = float(data['tier_2_rate'])
        if 'default_limit' in data: tariff.default_limit = float(data['default_limit'])
        
        db.session.commit()
        return jsonify({'message': 'Tariff updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
