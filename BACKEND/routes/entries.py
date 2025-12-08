from flask import Blueprint, request, jsonify
from modules import User, EnergyEntry, WaterEntry
from database import db
from datetime import datetime
from utils.helpers import (
    calculate_electricity_cost, 
    calculate_water_cost, 
    get_monthly_usage, 
    get_user_limits, 
    check_high_consumption
)

entries_bp = Blueprint('entries', __name__)

@entries_bp.route('/energy-entries', methods=['POST'])
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

@entries_bp.route('/water-entries', methods=['POST'])
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

@entries_bp.route('/preview/energy', methods=['POST'])
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


@entries_bp.route('/preview/water', methods=['POST'])
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
