# This is a patch file - the actual fix will be applied via terminal
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
        if 'user_category' in data:
            valid_categories = ['single', 'family', 'hostel', 'company']
            if data['user_category'] not in valid_categories:
                return jsonify({'error': 'Invalid user category'}), 400
            user.user_category = data['user_category']
        
        if 'family_members' in data:
            try:
                family_members = int(data['family_members'])
                if family_members < 1:
                    return jsonify({'error': 'Family members must be at least 1'}), 400
                user.family_members = family_members
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid family members value'}), 400
        
        if 'phone_number' in data:
            user.phone_number = data.get('phone_number', '')
        
        if 'custom_energy_limit' in data:
            try:
                limit = float(data['custom_energy_limit'])
                if limit < 0:
                    return jsonify({'error': 'Energy limit cannot be negative'}), 400
                user.custom_energy_limit = limit
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid energy limit value'}), 400
        
        if 'custom_water_limit' in data:
            try:
                limit = float(data['custom_water_limit'])
                if limit < 0:
                    return jsonify({'error': 'Water limit cannot be negative'}), 400
                user.custom_water_limit = limit
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid water limit value'}), 400
        
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
        return jsonify({'error': str(e)}), 500
