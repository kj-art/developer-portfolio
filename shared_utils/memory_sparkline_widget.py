import tkinter as tk
import time
import statistics
from collections import deque


class MemorySparklineWidget(tk.Canvas):
    """High-performance memory sparkline using tkinter Canvas with dynamic thresholds"""
    
    def __init__(self, parent, width=400, height=60, **kwargs):
        super().__init__(parent, width=width, height=height, 
                        highlightthickness=0, bg='#f8f9fa', **kwargs)
        
        self.width = width
        self.height = height
        self.padding = 4
        self.data = deque(maxlen=60)  # 60 seconds of data
        self.timestamps = deque(maxlen=60)
        
        # Dynamic thresholds
        self.baseline = 0
        self.yellow_threshold = 0
        self.red_threshold = 0
        
        # Visual styling
        self.line_color = "#2196F3"
        self.fill_color = "#E3F2FD"
        self.yellow_color = "#FF9800"
        self.red_color = "#F44336"
        self.grid_color = "#E0E0E0"
        self.text_color = "#424242"
        
        # Bind mouse events for interactivity
        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<Leave>", self._on_mouse_leave)
        
        self.tooltip_visible = False
        self.mouse_x = 0
    
    def add_data_point(self, memory_mb):
        """Add new memory data point and update display"""
        current_time = time.time()
        self.data.append(memory_mb)
        self.timestamps.append(current_time)
        
        self._update_thresholds()
        self._redraw()
    
    def _update_thresholds(self):
        """Calculate dynamic thresholds from data history"""
        if len(self.data) < 5:
            return
        
        data_list = list(self.data)
        
        if len(data_list) >= 20:
            # Statistical approach with sufficient data
            mean_val = statistics.mean(data_list)
            try:
                std_val = statistics.stdev(data_list)
                self.baseline = mean_val
                self.yellow_threshold = mean_val + std_val
                self.red_threshold = mean_val + (2 * std_val)
            except statistics.StatisticsError:
                # Fallback if standard deviation calculation fails
                self._percentage_thresholds(data_list)
        else:
            # Percentage-based approach with limited data
            self._percentage_thresholds(data_list)
    
    def _percentage_thresholds(self, data_list):
        """Calculate percentage-based thresholds"""
        mean_val = statistics.mean(data_list)
        self.baseline = mean_val
        self.yellow_threshold = mean_val * 1.25
        self.red_threshold = mean_val * 1.5
        
        # Ensure reasonable minimums
        self.yellow_threshold = max(self.yellow_threshold, mean_val + 10)
        self.red_threshold = max(self.red_threshold, mean_val + 25)
    
    def _redraw(self):
        """Redraw the entire sparkline"""
        self.delete("all")
        
        if len(self.data) < 2:
            self._draw_placeholder()
            return
        
        # Calculate drawing area
        draw_width = self.width - (2 * self.padding)
        draw_height = self.height - (2 * self.padding)
        
        # Calculate scale
        min_val = min(self.data)
        max_val = max(self.data)
        
        # Expand range to include thresholds for better visualization
        if self.red_threshold > 0:
            max_val = max(max_val, self.red_threshold * 1.1)
        
        value_range = max_val - min_val
        if value_range == 0:
            return
        
        # Draw grid lines
        self._draw_grid(min_val, max_val, draw_height)
        
        # Draw threshold lines
        self._draw_thresholds(min_val, max_val, draw_width, draw_height)
        
        # Calculate points for the sparkline
        points = self._calculate_points(min_val, max_val, draw_width, draw_height)
        
        # Draw filled area under line
        self._draw_filled_area(points, draw_height)
        
        # Draw main line with color transitions
        self._draw_line_with_colors(points, min_val, max_val)
        
        # Draw current value indicator
        self._draw_current_indicator(points)
        
        # Draw value labels
        self._draw_value_labels(min_val, max_val, draw_height)
        
        # Draw tooltip if mouse is over widget
        if self.tooltip_visible:
            self._draw_tooltip()
    
    def _draw_placeholder(self):
        """Draw placeholder when no data available"""
        center_x = self.width // 2
        center_y = self.height // 2
        
        self.create_text(center_x, center_y, text="Building memory baseline...", 
                        fill=self.text_color, font=('Arial', 9))
    
    def _draw_grid(self, min_val, max_val, draw_height):
        """Draw subtle grid lines"""
        # Horizontal grid lines
        for i in range(3):
            y = self.padding + (i * draw_height / 2)
            self.create_line(self.padding, y, self.width - self.padding, y, 
                           fill=self.grid_color, width=1)
    
    def _draw_thresholds(self, min_val, max_val, draw_width, draw_height):
        """Draw threshold lines"""
        value_range = max_val - min_val
        
        # Yellow threshold
        if min_val <= self.yellow_threshold <= max_val:
            y = self.height - self.padding - ((self.yellow_threshold - min_val) / value_range) * draw_height
            self.create_line(self.padding, y, self.width - self.padding, y, 
                           fill=self.yellow_color, width=2, dash=(4, 4))
            
            # Label
            self.create_text(self.width - self.padding - 2, y - 8, 
                           text=f"{self.yellow_threshold:.0f}MB", 
                           fill=self.yellow_color, font=('Arial', 8), anchor='e')
        
        # Red threshold
        if min_val <= self.red_threshold <= max_val:
            y = self.height - self.padding - ((self.red_threshold - min_val) / value_range) * draw_height
            self.create_line(self.padding, y, self.width - self.padding, y, 
                           fill=self.red_color, width=2, dash=(4, 4))
            
            # Label
            self.create_text(self.width - self.padding - 2, y - 8, 
                           text=f"{self.red_threshold:.0f}MB", 
                           fill=self.red_color, font=('Arial', 8), anchor='e')
    
    def _calculate_points(self, min_val, max_val, draw_width, draw_height):
        """Calculate line points for sparkline"""
        points = []
        value_range = max_val - min_val
        
        for i, value in enumerate(self.data):
            x = self.padding + (i / (len(self.data) - 1)) * draw_width
            y = self.height - self.padding - ((value - min_val) / value_range) * draw_height
            points.extend([x, y])
        
        return points
    
    def _draw_filled_area(self, points, draw_height):
        """Draw filled area under the sparkline"""
        if len(points) < 4:
            return
        
        # Create polygon points for filled area
        fill_points = ([self.padding, self.height - self.padding] + 
                      points + 
                      [self.width - self.padding, self.height - self.padding])
        
        self.create_polygon(fill_points, fill=self.fill_color, outline="", smooth=True)
    
    def _draw_line_with_colors(self, points, min_val, max_val):
        """Draw line with color transitions based on thresholds"""
        if len(points) < 4:
            return
        
        # Draw segments with appropriate colors
        for i in range(0, len(points) - 2, 2):
            x1, y1 = points[i], points[i + 1]
            x2, y2 = points[i + 2], points[i + 3]
            
            # Determine color based on value
            data_index = i // 2
            if data_index < len(self.data):
                value = self.data[data_index]
                color = self._get_value_color(value)
                
                self.create_line(x1, y1, x2, y2, fill=color, width=3, smooth=True)
    
    def _get_value_color(self, value):
        """Get color for value based on thresholds"""
        if value > self.red_threshold and self.red_threshold > 0:
            return self.red_color
        elif value > self.yellow_threshold and self.yellow_threshold > 0:
            return self.yellow_color
        else:
            return self.line_color
    
    def _draw_current_indicator(self, points):
        """Draw indicator for current value"""
        if len(points) < 2:
            return
        
        current_x, current_y = points[-2], points[-1]
        current_value = self.data[-1]
        
        # Circle indicator
        color = self._get_value_color(current_value)
        self.create_oval(current_x - 4, current_y - 4, current_x + 4, current_y + 4, 
                        fill=color, outline="white", width=2)
        
        # Current value text
        self.create_text(current_x, current_y - 15, text=f"{current_value:.1f}MB", 
                        fill=color, font=('Arial', 9, 'bold'), anchor='center')
    
    def _draw_value_labels(self, min_val, max_val, draw_height):
        """Draw min/max value labels"""
        # Min value
        self.create_text(self.padding + 2, self.height - self.padding - 2, 
                        text=f"{min_val:.1f}", fill=self.text_color, 
                        font=('Arial', 8), anchor='sw')
        
        # Max value
        self.create_text(self.padding + 2, self.padding + 2, 
                        text=f"{max_val:.1f}", fill=self.text_color, 
                        font=('Arial', 8), anchor='nw')
    
    def _on_mouse_move(self, event):
        """Handle mouse movement for tooltip"""
        self.mouse_x = event.x
        self.tooltip_visible = True
        self._redraw()
    
    def _on_mouse_leave(self, event):
        """Handle mouse leaving widget"""
        self.tooltip_visible = False
        self._redraw()
    
    def _draw_tooltip(self):
        """Draw tooltip showing value at mouse position"""
        if len(self.data) < 2:
            return
        
        # Calculate which data point mouse is over
        data_width = self.width - (2 * self.padding)
        relative_x = max(0, min(data_width, self.mouse_x - self.padding))
        data_index = int((relative_x / data_width) * (len(self.data) - 1))
        
        if 0 <= data_index < len(self.data):
            value = self.data[data_index]
            timestamp = self.timestamps[data_index]
            
            # Format time (seconds ago)
            seconds_ago = int(time.time() - timestamp)
            time_text = f"{seconds_ago}s ago" if seconds_ago > 0 else "now"
            
            # Position tooltip
            tooltip_x = self.mouse_x
            tooltip_y = 20
            
            # Draw tooltip background
            tooltip_text = f"{value:.1f}MB ({time_text})"
            bbox = self.create_text(tooltip_x, tooltip_y, text=tooltip_text, 
                                  font=('Arial', 9), anchor='center')
            
            # Get text bounds for background
            text_bbox = self.bbox(bbox)
            if text_bbox:
                x1, y1, x2, y2 = text_bbox
                self.create_rectangle(x1 - 4, y1 - 2, x2 + 4, y2 + 2, 
                                    fill='white', outline='gray', tags='tooltip_bg')
                
                # Move text to front
                self.tag_raise(bbox)