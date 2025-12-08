from flask import Blueprint, request, jsonify, Response
from modules import User, EnergyEntry, WaterEntry
from database import db
from datetime import datetime, timedelta
import csv
import io
from utils.helpers import get_monthly_usage, get_user_limits, generate_conservation_tips

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/<int:user_id>', methods=['GET'])
def get_dashboard(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get data for the current week (or last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Previous week dates (for comparison)
        prev_end_date = start_date
        prev_start_date = prev_end_date - timedelta(days=7)
        
        # Get energy and water entries for the current week
        energy_entries = EnergyEntry.query.filter(
            EnergyEntry.user_id == user_id,
            EnergyEntry.reading_date >= start_date,
            EnergyEntry.reading_date <= end_date
        ).all()
        
        water_entries = WaterEntry.query.filter(
            WaterEntry.user_id == user_id,
            WaterEntry.reading_date >= start_date,
            WaterEntry.reading_date <= end_date
        ).all()
        
        # Get energy and water entries for the PREVIOUS week
        prev_energy_entries = EnergyEntry.query.filter(
            EnergyEntry.user_id == user_id,
            EnergyEntry.reading_date >= prev_start_date,
            EnergyEntry.reading_date < prev_end_date
        ).all()
        
        prev_water_entries = WaterEntry.query.filter(
            WaterEntry.user_id == user_id,
            WaterEntry.reading_date >= prev_start_date,
            WaterEntry.reading_date < prev_end_date
        ).all()
        
        # Calculate weekly totals
        total_energy = sum(e.electricity_usage for e in energy_entries)
        total_water = sum(w.water_usage for w in water_entries)
        total_cost = sum(e.cost for e in energy_entries) + sum(w.cost for w in water_entries)
        
        # Calculate PREVIOUS weekly totals
        prev_total_energy = sum(e.electricity_usage for e in prev_energy_entries)
        prev_total_water = sum(w.water_usage for w in prev_water_entries)
        
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
            'prev_weekly_energy_used': prev_total_energy,
            'prev_weekly_water_used': prev_total_water,
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

@dashboard_bp.route('/chart-data/<int:user_id>', methods=['GET'])
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
        
        # Build daily data arrays for the 7 days (non-cumulative)
        dates = []
        energy_data = [] # Daily usage
        water_data = []  # Daily usage
        cumulative_energy = 0
        cumulative_water = 0
        
        # Determine daily limits for comparison
        daily_energy_limit = monthly_energy_limit / 30
        daily_water_limit = monthly_water_limit / 30
        
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
            
            energy_data.append(round(day_energy, 2))
            water_data.append(round(day_water, 2))
        
        # Calculate when resources will end (project based on daily average)
        avg_daily_energy = cumulative_energy / 7 if cumulative_energy > 0 else 0
        avg_daily_water = cumulative_water / 7 if cumulative_water > 0 else 0
        
        # Days used in the 7-day week (how many days have passed since start_date)
        days_elapsed = (end_date.date() - start_date.date()).days
        days_remaining_in_week = 7 - days_elapsed
        
        # Calculate days until limit exceeded (based on monthly limit vs projected monthly usage)
        # Simplified: Estimate using daily avg vs daily limit
        
        # Calculate end dates based on the weekly limit
        # For projection, we can still use the cumulative logic logic internally or just return N/A
        energy_limit_date = 'N/A' 
        water_limit_date = 'N/A'
        
        energy_days_until_limit = float('inf')
        water_days_until_limit = float('inf')
        
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
            'energy_limit': daily_energy_limit, # Send DAILY limit for chart
            'water_limit': daily_water_limit,   # Send DAILY limit for chart
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

@dashboard_bp.route('/analytics/<int:user_id>', methods=['GET'])
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

        # Generate tips
        tips = generate_conservation_tips(energy_entries, water_entries, user)

        return jsonify({
            'total_energy': total_energy,
            'total_water': total_water,
            'total_cost': total_cost,
            'series': series,
            'conservation_tips': tips
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/export/<int:user_id>', methods=['GET'])
def export_data(user_id):
    try:
        start_str = request.args.get('start_date')
        end_str = request.args.get('end_date')

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

        # Create CSV
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(['Date', 'Type', 'Usage', 'Unit', 'Cost (MWK)'])

        for e in energy_entries:
            cw.writerow([e.reading_date.strftime('%Y-%m-%d'), 'Electricity', e.electricity_usage, 'kWh', e.cost])
        
        for w in water_entries:
            cw.writerow([w.reading_date.strftime('%Y-%m-%d'), 'Water', w.water_usage, 'Liters', w.cost])

        output = si.getvalue()
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=usage_report.csv"}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
