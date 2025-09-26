#!/usr/bin/env python3
"""
StringSmith Memory Visualization Examples

Shows different ways to display memory usage data using StringSmith's
conditional formatting and custom functions.
"""

import sys
import os
import random
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from shared_utils.stringsmith import TemplateFormatter


def demo_ascii_bar_charts():
    """ASCII bar charts with color coding"""
    print("=" * 60)
    print("ASCII BAR CHARTS WITH COLOR CODING")
    print("=" * 60)
    
    # Sample memory data (MB over time)
    memory_data = [
        (0, 45.2), (5, 52.1), (10, 78.5), (15, 95.3), (20, 112.7),
        (25, 125.4), (30, 98.2), (35, 87.6), (40, 76.3), (45, 68.1)
    ]
    
    max_memory = max(mem for _, mem in memory_data)
    
    def memory_color(usage_mb):
        if usage_mb > 100:
            return 'red'
        elif usage_mb > 75:
            return 'yellow'
        return 'green'
    
    def make_bar(usage_mb):
        bar_width = 40
        filled = int((usage_mb / max_memory) * bar_width)
        return '█' * filled + '░' * (bar_width - filled)
    
    formatter = TemplateFormatter(
        "{{Time ;timestamp;s:}} {{#memory_color;{$make_bar}memory_mb;MB}}",
        functions={
            'memory_color': memory_color,
            'make_bar': make_bar
        }
    )
    
    for timestamp, memory_mb in memory_data:
        result = formatter.format(timestamp=f"{timestamp:2d}", memory_mb=memory_mb)
        print(result)


def demo_sparkline_charts():
    """Compact sparkline-style memory visualization"""
    print("\n" + "=" * 60)
    print("SPARKLINE MEMORY VISUALIZATION")
    print("=" * 60)
    
    # More detailed memory data
    memory_values = [45, 48, 52, 58, 65, 72, 85, 92, 105, 118, 125, 120, 110, 98, 87, 75, 68, 62]
    
    def get_spark_char(value, values):
        """Convert value to sparkline character"""
        min_val, max_val = min(values), max(values)
        if max_val == min_val:
            return '▄'
        
        normalized = (value - min_val) / (max_val - min_val)
        if normalized >= 0.875:
            return '█'
        elif normalized >= 0.75:
            return '▇'
        elif normalized >= 0.625:
            return '▆'
        elif normalized >= 0.5:
            return '▅'
        elif normalized >= 0.375:
            return '▄'
        elif normalized >= 0.25:
            return '▃'
        elif normalized >= 0.125:
            return '▂'
        else:
            return '▁'
    
    def memory_trend_color(current_mb, peak_mb):
        if current_mb > peak_mb * 0.9:
            return 'red'
        elif current_mb > peak_mb * 0.7:
            return 'yellow'
        return 'green'
    
    # Build sparkline
    sparkline = ''.join(get_spark_char(val, memory_values) for val in memory_values)
    current_memory = memory_values[-1]
    peak_memory = max(memory_values)
    
    formatter = TemplateFormatter(
        "{{Memory Usage: ;{#memory_trend_color}{$get_sparkline}current_mb;MB}} "
        "{{(Peak: ;peak_mb;MB)}} {{#trend_arrow;{$trend_indicator}trend;}}",
        functions={
            'memory_trend_color': lambda mb: memory_trend_color(mb, peak_memory),
            'get_sparkline': lambda _: sparkline,
            'trend_arrow': lambda trend: 'red' if trend == '↗' else 'green' if trend == '↘' else 'yellow',
            'trend_indicator': lambda _: '↗' if current_memory > memory_values[-3] else '↘' if current_memory < memory_values[-3] else '→'
        }
    )
    
    result = formatter.format(
        sparkline="", 
        current_mb=current_memory, 
        peak_mb=peak_memory,
        trend=""
    )
    print(result)


def demo_real_time_status():
    """Real-time memory status updates"""
    print("\n" + "=" * 60)
    print("REAL-TIME MEMORY STATUS (simulated)")
    print("=" * 60)
    
    def status_color(usage_mb):
        if usage_mb > 200:
            return 'red'
        elif usage_mb > 100:
            return 'yellow'
        return 'green'
    
    def status_icon(usage_mb):
        if usage_mb > 200:
            return '🚨'
        elif usage_mb > 100:
            return '⚠️'
        return '✅'
    
    def memory_percentage(current, max_available=512):
        return f"{(current/max_available)*100:.1f}%"
    
    def is_critical(usage_mb):
        return usage_mb > 200
    
    def format_delta(delta_mb):
        if abs(delta_mb) < 0.1:
            return "stable"
        sign = "+" if delta_mb > 0 else ""
        return f"{sign}{delta_mb:.1f}MB"
    
    formatter = TemplateFormatter(
        "{{$status_icon}} {{#status_color;Memory: ;current_mb;MB}} "
        "{{({$memory_percentage}percent; of available)}} "
        "{{Delta: ;{$format_delta}delta;}} "
        "{{?is_critical;🔥 CRITICAL - REDUCE MEMORY USAGE;current_mb;}}",
        functions={
            'status_color': status_color,
            'status_icon': status_icon,
            'memory_percentage': memory_percentage,
            'is_critical': is_critical,
            'format_delta': format_delta
        }
    )
    
    # Simulate real-time updates
    memory_values = [45.2, 67.8, 89.1, 125.6, 178.3, 234.7, 198.4, 156.2]
    previous = 45.2
    
    for current in memory_values:
        delta = current - previous
        result = formatter.format(
            current_mb=current,
            percent="",
            delta=delta
        )
        print(result)
        previous = current
        time.sleep(0.5)  # Simulate real-time updates


def demo_memory_report():
    """Comprehensive memory usage report"""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE MEMORY REPORT")
    print("=" * 60)
    
    # Sample processing statistics
    stats = {
        'start_memory': 42.3,
        'peak_memory': 156.8,
        'end_memory': 68.4,
        'average_memory': 89.2,
        'processing_time': 45.7,
        'files_processed': 247,
        'total_rows': 125000
    }
    
    def efficiency_color(mb_per_file):
        if mb_per_file > 2.0:
            return 'red'
        elif mb_per_file > 1.0:
            return 'yellow'
        return 'green'
    
    def trend_analysis(start, peak, end):
        if end > start * 1.5:
            return 'memory leak detected'
        elif end < start * 0.8:
            return 'efficient cleanup'
        return 'normal behavior'
    
    def memory_grade(efficiency):
        print(efficiency)
        if efficiency < 0.5:
            return 'A'
        elif efficiency < 1.0:
            return 'B'
        elif efficiency < 2.0:
            return 'C'
        return 'D'
    
    def format_efficiency(mb_per_file):
        return f"{mb_per_file:.2f}MB/file"
    
    def needs_optimization(grade):
        return grade in ['C', 'D']
    
    formatter = TemplateFormatter(
        "{{#FF6B35@bold;📊 MEMORY USAGE REPORT}}\n"
        "{{├── Peak Usage: ;{#peak_color}{$format_peak}peak_memory;}}\n"
        "{{├── Final Usage: ;end_memory;MB}}{{ (;{$format_cleanup}cleanup;)}}\n"
        "{{├── Processing Efficiency: ;{#efficiency_color}{$format_efficiency}efficiency;}} {{Grade: ;{#grade_color}{$memory_grade}grade;}}\n"
        "{{├── Trend Analysis: ;{$trend_analysis}trend;}}\n"
        "{{└── Files/Memory Ratio: ;files_processed; files / }}{{;average_memory;MB avg}}\n"
        "{{?needs_optimization;\n⚠️  OPTIMIZATION RECOMMENDED: Consider streaming processing for better memory efficiency;grade;}}",
        functions={
            'peak_color': lambda mb: 'red' if mb > 150 else 'yellow' if mb > 100 else 'green',
            'efficiency_color': efficiency_color,
            'grade_color': lambda grade: 'green' if grade in ['A', 'B'] else 'yellow' if grade == 'C' else 'red',
            'format_peak': lambda mb: f"{mb:.1f}MB",
            'format_cleanup': lambda end_start: f"↘ {((stats['start_memory'] - end_start) / stats['start_memory'] * 100):.1f}% reduction",
            'format_efficiency': format_efficiency,
            'memory_grade': memory_grade,
            'trend_analysis': lambda _: trend_analysis(stats['start_memory'], stats['peak_memory'], stats['end_memory']),
            'needs_optimization': needs_optimization
        }
    )
    
    efficiency = stats['peak_memory'] / stats['files_processed']
    grade = memory_grade(efficiency)
    
    result = formatter.format(
        peak_memory=stats['peak_memory'],
        end_memory=stats['end_memory'],
        efficiency=efficiency,
        grade=grade,
        trend="",
        files_processed=stats['files_processed'],
        average_memory=stats['average_memory'],
        cleanup=stats['end_memory']
    )
    print(result)


def demo_gui_status_bar():
    """Memory status for GUI status bar"""
    print("\n" + "=" * 60)
    print("GUI STATUS BAR MEMORY INDICATORS")
    print("=" * 60)
    
    def compact_status_color(usage_mb):
        if usage_mb > 150:
            return 'red'
        elif usage_mb > 100:
            return 'yellow'
        return 'green'
    
    def compact_icon(usage_mb):
        if usage_mb > 150:
            return '●'
        elif usage_mb > 100:
            return '●'
        return '●'
    
    formatter = TemplateFormatter(
        "{{Processing... }} {{Files: ;files_done}}/{{total_files}} "
        "{{#compact_status_color;;{$compact_icon}memory_mb;MB}} "
        "{{?show_eta;ETA: ;eta;}}",
        functions={
            'compact_status_color': compact_status_color,
            'compact_icon': compact_icon,
            'show_eta': lambda eta: eta is not None
        }
    )
    
    # Simulate different processing states
    states = [
        {'files_done': 25, 'total_files': 100, 'memory_mb': 67.2, 'eta': '2m 15s'},
        {'files_done': 50, 'total_files': 100, 'memory_mb': 89.4, 'eta': '1m 45s'},
        {'files_done': 75, 'total_files': 100, 'memory_mb': 125.8, 'eta': '45s'},
        {'files_done': 100, 'total_files': 100, 'memory_mb': 78.3, 'eta': None}
    ]
    
    for state in states:
        result = formatter.format(memory="", **state)
        print(f"Status Bar: {result}")


def main():
    """Run all memory visualization demos"""
    print("StringSmith Memory Visualization Examples")
    print("Demonstrating different approaches to displaying memory usage data\n")
    
    demo_ascii_bar_charts()
    demo_sparkline_charts()
    demo_real_time_status()
    demo_memory_report()
    demo_gui_status_bar()
    
    print("\n" + "=" * 60)
    print("ALL DEMOS COMPLETE")
    print("=" * 60)
    print("StringSmith provides flexible text-based memory visualization")
    print("Perfect for console apps, status bars, and reporting systems!")


if __name__ == "__main__":
    main()