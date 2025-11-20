"""
Enhanced Charting Module - Professional Time-Series Visualization
Creates line charts with proper X/Y axes, date labels, and time-series tracking
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
from datetime import datetime
from typing import Dict, List
import json
import os
from config.settings import RESOURCE_LIMITS, COLORS, MARKERS, GRAPH_SETTINGS


class EnhancedCharts:
    """Generates professional time-series charts with proper axes and date tracking"""
    
    def __init__(self, output_dir='graphs'):
        self.output_dir = output_dir
        self.limits = RESOURCE_LIMITS
        self.colors = COLORS
        self.markers = MARKERS
        self.settings = GRAPH_SETTINGS
        self.ensure_output_dir()
    
    def ensure_output_dir(self):
        """Create output directory if it doesn't exist"""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def parse_dates(self, date_strings: List[str]) -> List[datetime]:
        """Parse date strings to datetime objects"""
        return [datetime.strptime(date_str, '%Y-%m-%d') for date_str in date_strings]
    
    def create_tracking_timeline(self,
                                dates: List[str],
                                water_values: List[float],
                                electricity_values: List[float],
                                title: str = 'Resource Consumption Tracking Timeline',
                                output_file: str = 'tracking_timeline.png') -> str:
        """
        Create comprehensive time-series tracking chart with both resources
        Shows clear X-axis (dates) and Y-axis (values) with proper scaling
        """
        date_objects = self.parse_dates(dates)
        water_limit = self.limits['water']['limit']
        electricity_limit = self.limits['electricity']['limit']
        
        # Create figure with two Y-axes for different scales
        fig, ax1 = plt.subplots(
            figsize=self.settings['figure_size'],
            dpi=self.settings['dpi']
        )
        
        # ===== PRIMARY AXIS (Water - Left) =====
        color_water = self.colors['water']
        ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Water Consumption (L/week)', fontsize=11, fontweight='bold', color=color_water)
        ax1.tick_params(axis='y', labelcolor=color_water)
        
        # Plot water line
        line1 = ax1.plot(
            date_objects,
            water_values,
            color=color_water,
            marker=self.markers['water'],
            markersize=self.settings['marker_size'],
            linewidth=self.settings['line_width'],
            label='Water Consumption',
            alpha=0.8
        )
        
        # Water limit line
        ax1.axhline(
            y=water_limit,
            color=color_water,
            linestyle=self.settings['limit_line_style'],
            linewidth=self.settings['limit_line_width'],
            alpha=0.5,
            label=f'Water Limit ({water_limit} L/week)'
        )
        
        # ===== SECONDARY AXIS (Electricity - Right) =====
        ax2 = ax1.twinx()
        color_electricity = self.colors['electricity']
        ax2.set_ylabel('Electricity Consumption (kWh/week)', fontsize=11, fontweight='bold', color=color_electricity)
        ax2.tick_params(axis='y', labelcolor=color_electricity)
        
        # Plot electricity line
        line2 = ax2.plot(
            date_objects,
            electricity_values,
            color=color_electricity,
            marker=self.markers['electricity'],
            markersize=self.settings['marker_size'],
            linewidth=self.settings['line_width'],
            label='Electricity Consumption',
            alpha=0.8
        )
        
        # Electricity limit line
        ax2.axhline(
            y=electricity_limit,
            color=color_electricity,
            linestyle=self.settings['limit_line_style'],
            linewidth=self.settings['limit_line_width'],
            alpha=0.5,
            label=f'Electricity Limit ({electricity_limit} kWh/week)'
        )
        
        # ===== X-AXIS FORMATTING (Dates) =====
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45, ha='right', fontsize=10)
        
        # ===== TITLE AND GRID =====
        ax1.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax1.grid(
            self.settings['grid'],
            alpha=self.settings['grid_alpha'],
            linestyle='-',
            linewidth=0.5
        )
        ax1.set_axisbelow(True)
        
        # ===== COMBINED LEGEND =====
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left', fontsize=10, framealpha=0.95, edgecolor='black')
        
        # ===== LAYOUT =====
        fig.tight_layout()
        
        # Save graph
        full_path = os.path.join(self.output_dir, output_file)
        plt.savefig(full_path, dpi=self.settings['dpi'], bbox_inches='tight')
        plt.close()
        
        return full_path
    
    def create_weekly_tracking_chart(self,
                                    dates: List[str],
                                    values: List[float],
                                    resource_type: str = 'water',
                                    title: str = None,
                                    output_file: str = None) -> str:
        """
        Create individual time-series chart for single resource
        Shows week-by-week tracking with dates on X-axis
        """
        if title is None:
            title = f"{resource_type.capitalize()} Consumption Tracking (Per Week)"
        if output_file is None:
            output_file = f"{resource_type}_weekly_tracking.png"
        
        date_objects = self.parse_dates(dates)
        
        if resource_type == 'water':
            limit = self.limits['water']['limit']
            unit = self.limits['water']['unit']
            color = self.colors['water']
            marker = self.markers['water']
        else:
            limit = self.limits['electricity']['limit']
            unit = self.limits['electricity']['unit']
            color = self.colors['electricity']
            marker = self.markers['electricity']
        
        fig, ax = plt.subplots(
            figsize=self.settings['figure_size'],
            dpi=self.settings['dpi']
        )
        
        # Plot line with markers
        ax.plot(
            date_objects,
            values,
            color=color,
            marker=marker,
            markersize=self.settings['marker_size'],
            linewidth=self.settings['line_width'],
            label='Weekly Consumption',
            alpha=0.8
        )
        
        # Add data point labels
        for date_obj, value in zip(date_objects, values):
            ax.annotate(
                f'{value:.0f} {unit.split("/")[0]}',
                xy=(date_obj, value),
                xytext=(0, 10),
                textcoords='offset points',
                ha='center',
                fontsize=9,
                fontweight='bold'
            )
        
        # Limit line
        ax.axhline(
            y=limit,
            color=color,
            linestyle=self.settings['limit_line_style'],
            linewidth=self.settings['limit_line_width'],
            alpha=0.5,
            label=f'Weekly Limit ({limit} {unit})'
        )
        
        # Fill between to highlight over/under
        ax.fill_between(
            date_objects,
            values,
            limit,
            where=[v >= limit for v in values],
            alpha=0.2,
            color=self.colors['over_limit'],
            label='Over Limit'
        )
        ax.fill_between(
            date_objects,
            values,
            limit,
            where=[v < limit for v in values],
            alpha=0.1,
            color=self.colors['under_limit'],
            label='Under Limit'
        )
        
        # Styling
        ax.set_xlabel('Week Starting Date', fontsize=12, fontweight='bold')
        ax.set_ylabel(f'{resource_type.capitalize()} Consumption ({unit})', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        # X-axis date formatting
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45, ha='right', fontsize=10)
        
        # Y-axis scaling
        ax.yaxis.set_major_locator(MaxNLocator(integer=False))
        y_min, y_max = min(values), max(values)
        y_margin = (y_max - y_min) * 0.1 if (y_max - y_min) > 0 else limit * 0.1
        ax.set_ylim(max(0, y_min - y_margin), max(limit, y_max + y_margin))
        
        # Grid and legend
        ax.grid(self.settings['grid'], alpha=self.settings['grid_alpha'])
        ax.set_axisbelow(True)
        ax.legend(loc='best', fontsize=10, framealpha=0.95, edgecolor='black')
        
        plt.tight_layout()
        
        full_path = os.path.join(self.output_dir, output_file)
        plt.savefig(full_path, dpi=self.settings['dpi'], bbox_inches='tight')
        plt.close()
        
        return full_path
    
    def create_week_by_week_comparison(self,
                                      weeks: List[str],
                                      water_values: List[float],
                                      electricity_values: List[float],
                                      output_file: str = 'week_comparison.png') -> str:
        """
        Create side-by-side comparison of water vs electricity per week
        Shows both resources with clear week labels on X-axis
        """
        x_pos = range(len(weeks))
        width = 0.35
        
        fig, ax = plt.subplots(
            figsize=self.settings['figure_size'],
            dpi=self.settings['dpi']
        )
        
        water_limit = self.limits['water']['limit']
        electricity_limit = self.limits['electricity']['limit']
        
        # Determine colors based on limit status
        water_colors = [
            self.colors['over_limit'] if val > water_limit else self.colors['water']
            for val in water_values
        ]
        electricity_colors = [
            self.colors['over_limit'] if val > electricity_limit else self.colors['electricity']
            for val in electricity_values
        ]
        
        # Plot bars
        bars1 = ax.bar(
            [p - width/2 for p in x_pos],
            water_values,
            width,
            label='Water (L/week)',
            color=water_colors,
            alpha=0.8,
            edgecolor='black',
            linewidth=1.5
        )
        
        bars2 = ax.bar(
            [p + width/2 for p in x_pos],
            electricity_values,
            width,
            label='Electricity (kWh/week)',
            color=electricity_colors,
            alpha=0.8,
            edgecolor='black',
            linewidth=1.5
        )
        
        # Add limit reference lines
        ax.axhline(y=water_limit, color=self.colors['water'], linestyle='--',
                   linewidth=2, alpha=0.6, label=f'Water Limit ({water_limit})')
        ax.axhline(y=electricity_limit, color=self.colors['electricity'], linestyle='--',
                   linewidth=2, alpha=0.6, label=f'Electricity Limit ({electricity_limit})')
        
        # Value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.0f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom',
                           fontsize=9, fontweight='bold')
        
        # Styling
        ax.set_xlabel('Week', fontsize=12, fontweight='bold')
        ax.set_ylabel('Consumption', fontsize=12, fontweight='bold')
        ax.set_title('Weekly Resource Consumption Comparison', fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(weeks, rotation=45, ha='right')
        ax.grid(axis='y', alpha=0.3)
        ax.set_axisbelow(True)
        ax.legend(loc='best', fontsize=10, framealpha=0.95, edgecolor='black')
        
        plt.tight_layout()
        
        full_path = os.path.join(self.output_dir, output_file)
        plt.savefig(full_path, dpi=self.settings['dpi'], bbox_inches='tight')
        plt.close()
        
        return full_path


def main():
    """Demo usage"""
    dates = ['2024-01-01', '2024-01-08', '2024-01-15']
    water = [800, 1100, 900]
    electricity = [400, 550, 450]
    
    charts = EnhancedCharts()
    
    print("Generating enhanced tracking charts...")
    
    # Time-series tracking
    tracking = charts.create_tracking_timeline(dates, water, electricity)
    print(f"✅ Tracking timeline: {tracking}")
    
    # Individual weekly charts
    water_chart = charts.create_weekly_tracking_chart(dates, water, 'water')
    print(f"✅ Water weekly chart: {water_chart}")
    
    elec_chart = charts.create_weekly_tracking_chart(dates, electricity, 'electricity')
    print(f"✅ Electricity weekly chart: {elec_chart}")
    
    # Week comparison
    weeks = ['Week 1', 'Week 2', 'Week 3']
    comparison = charts.create_week_by_week_comparison(weeks, water, electricity)
    print(f"✅ Week comparison: {comparison}")


if __name__ == '__main__':
    main()
