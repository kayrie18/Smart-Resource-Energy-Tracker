"""
Enhanced Resource Tracker - Fixed Version
Properly handles weekly tracking, date ranges, and units display
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from config.settings import RESOURCE_LIMITS

class EnhancedResourceTracker:
    """Enhanced tracker with proper weekly tracking and date range support"""
    
    def __init__(self, data_file='data/resources.json'):
        self.data_file = data_file
        self.limits = RESOURCE_LIMITS
        self.ensure_data_file_exists()
    
    def ensure_data_file_exists(self):
        """Create data file if it doesn't exist"""
        if not os.path.exists(self.data_file):
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            self.save_data({'entries': []})
    
    def load_data(self) -> Dict:
        """Load resource data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {'entries': []}
    
    def save_data(self, data: Dict):
        """Save resource data to JSON file"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_week_info(self, date_str: str) -> Dict:
        """Get comprehensive week information from date string"""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        year, week, weekday = date_obj.isocalendar()
        
        # Calculate week start (Monday) and end (Sunday)
        week_start = date_obj - timedelta(days=weekday - 1)
        week_end = week_start + timedelta(days=6)
        
        return {
            'year': year,
            'week': week,
            'week_key': f"{year}-W{week:02d}",
            'week_start': week_start.strftime('%Y-%m-%d'),
            'week_end': week_end.strftime('%Y-%m-%d'),
            'weekday': weekday
        }
    
    def check_limit_status(self, resource: str, value: float) -> Tuple[str, float, str]:
        """
        Check if resource usage is over/under limit
        Returns: (status, remaining_capacity, unit)
        """
        limit = self.limits[resource]['limit']
        unit = self.limits[resource]['unit']
        remaining = limit - value
        
        if value > limit:
            status = 'over_limit'
        elif value == limit:
            status = 'at_limit'
        else:
            status = 'under_limit'
        
        return status, remaining, unit
    
    def add_entry(self, date: str, water: float, electricity: float) -> Dict:
        """
        Add a new resource consumption entry with week info
        Returns: entry with complete tracking information
        """
        data = self.load_data()
        
        water_status, water_remaining, water_unit = self.check_limit_status('water', water)
        elec_status, elec_remaining, elec_unit = self.check_limit_status('electricity', electricity)
        
        week_info = self.get_week_info(date)
        entry_id = max([e.get('id', 0) for e in data['entries']], default=0) + 1
        
        entry = {
            'id': entry_id,
            'date': date,
            'week_key': week_info['week_key'],
            'week_start': week_info['week_start'],
            'week_end': week_info['week_end'],
            'water': water,
            'water_unit': water_unit,
            'electricity': electricity,
            'electricity_unit': elec_unit,
            'water_status': water_status,
            'water_remaining': water_remaining,
            'electricity_status': elec_status,
            'electricity_remaining': elec_remaining,
            'timestamp': datetime.now().isoformat()
        }
        
        data['entries'].append(entry)
        self.save_data(data)
        return entry
    
    def get_entries_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get entries within a date range with complete info"""
        data = self.load_data()
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        filtered_entries = []
        for entry in data['entries']:
            entry_date = datetime.strptime(entry['date'], '%Y-%m-%d')
            if start <= entry_date <= end:
                filtered_entries.append(entry)
        
        return sorted(filtered_entries, key=lambda x: x['date'])
    
    def get_weekly_summary(self, start_date: str = None, end_date: str = None) -> Dict:
        """
        Get summary of entries with weekly aggregates and week boundaries
        Shows week start/end dates clearly with proper units
        """
        data = self.load_data()
        entries_to_process = data['entries']
        
        # Filter by date range if provided
        if start_date and end_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            entries_to_process = [
                e for e in entries_to_process
                if start <= datetime.strptime(e['date'], '%Y-%m-%d') <= end
            ]
        
        summary = {}
        
        for entry in entries_to_process:
            week_key = entry.get('week_key', 'unknown')
            
            if week_key not in summary:
                summary[week_key] = {
                    'week_start': entry.get('week_start'),
                    'week_end': entry.get('week_end'),
                    'water_total': 0,
                    'water_unit': self.limits['water']['unit'],
                    'electricity_total': 0,
                    'electricity_unit': self.limits['electricity']['unit'],
                    'water_limit': self.limits['water']['limit'],
                    'electricity_limit': self.limits['electricity']['limit'],
                    'entries_count': 0,
                    'water_status': 'under_limit',
                    'electricity_status': 'under_limit'
                }
            
            summary[week_key]['water_total'] += entry.get('water', 0)
            summary[week_key]['electricity_total'] += entry.get('electricity', 0)
            summary[week_key]['entries_count'] += 1
            
            # Update status if any entry is over limit
            if entry.get('water_status') == 'over_limit':
                summary[week_key]['water_status'] = 'over_limit'
            if entry.get('electricity_status') == 'over_limit':
                summary[week_key]['electricity_status'] = 'over_limit'
        
        return summary
    
    def get_all_entries(self) -> List[Dict]:
        """Get all tracking entries sorted by date"""
        data = self.load_data()
        return sorted(data.get('entries', []), key=lambda x: x.get('date', ''))
    
    def export_detailed_report(self, start_date: str, end_date: str) -> Dict:
        """
        Export detailed report with proper formatting and units
        Perfect for PDF/CSV export with all tracking information
        """
        entries = self.get_entries_by_date_range(start_date, end_date)
        summary = self.get_weekly_summary(start_date, end_date)
        
        report = {
            'report_generated': datetime.now().isoformat(),
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            },
            'entries_count': len(entries),
            'entries': entries,
            'weekly_summary': summary,
            'resource_limits': {
                'water': {
                    'limit': self.limits['water']['limit'],
                    'unit': self.limits['water']['unit']
                },
                'electricity': {
                    'limit': self.limits['electricity']['limit'],
                    'unit': self.limits['electricity']['unit']
                }
            }
        }
        
        return report
    
    def clear_data(self):
        """Clear all tracking data"""
        self.save_data({'entries': []})


def main():
    """Demo of enhanced tracker"""
    tracker = EnhancedResourceTracker()
    
    print("\n🎯 ENHANCED RESOURCE TRACKER - DEMO\n")
    
    # Add test data with proper dates
    test_dates = [
        ('2024-01-01', 800, 400),
        ('2024-01-08', 1100, 550),  # Over limits
        ('2024-01-15', 900, 450)
    ]
    
    print("Adding entries with complete week tracking...\n")
    for date, water, electricity in test_dates:
        entry = tracker.add_entry(date, water, electricity)
        print(f"✅ {entry['date']}: {entry['water']} {entry['water_unit']}, {entry['electricity']} {entry['electricity_unit']}")
        print(f"   Week: {entry['week_start']} to {entry['week_end']}")
        print(f"   Water Status: {entry['water_status']} ({entry['water_remaining']} {entry['water_unit']} remaining)")
        print(f"   Electricity Status: {entry['electricity_status']} ({entry['electricity_remaining']} {entry['electricity_unit']} remaining)\n")
    
    # Weekly summary
    print("\n📊 WEEKLY SUMMARY:\n")
    summary = tracker.get_weekly_summary('2024-01-01', '2024-01-31')
    for week_key, week_data in sorted(summary.items()):
        print(f"Week: {week_key} ({week_data['week_start']} to {week_data['week_end']})")
        print(f"  💧 Water: {week_data['water_total']} {week_data['water_unit']} / {week_data['water_limit']} {week_data['water_unit']} [{week_data['water_status']}]")
        print(f"  ⚡ Electricity: {week_data['electricity_total']} {week_data['electricity_unit']} / {week_data['electricity_limit']} {week_data['electricity_unit']} [{week_data['electricity_status']}]\n")


if __name__ == '__main__':
    main()
