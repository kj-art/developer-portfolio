"""
Memory monitoring system for GUI applications.

Provides real-time memory usage tracking with configurable callbacks for status updates
and integration with sparkline widgets for visual representation.
"""

import time
from typing import Optional, Callable, Protocol

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class SparklineWidget(Protocol):
    """Protocol for sparkline widgets that can display memory data"""
    def add_data_point(self, value: float) -> None: ...
    @property
    def data(self) -> any: ...
    @property
    def baseline(self) -> float: ...
    @property
    def yellow_threshold(self) -> float: ...
    @property
    def red_threshold(self) -> float: ...


class MemoryMonitor:
    """
    Real-time memory monitoring with callback-based status updates.
    
    Tracks process memory usage and provides formatted status text with trend analysis.
    Integrates with sparkline widgets for visual representation and supports configurable
    update intervals and status callbacks.
    """
    
    def __init__(self, 
                 update_interval_ms: int = 1000,
                 status_callback: Optional[Callable[[str], None]] = None,
                 scheduler_callback: Optional[Callable[[int, Callable], None]] = None):
        """
        Initialize memory monitor with callback configuration.
        
        Args:
            update_interval_ms: Update frequency in milliseconds
            status_callback: Function called with formatted status text
            scheduler_callback: Function to schedule next update (e.g., tkinter's after())
        """
        self.update_interval_ms = update_interval_ms
        self.status_callback = status_callback
        self.scheduler_callback = scheduler_callback
        
        self.is_active = False
        self.process = None
        self.sparkline_widget: Optional[SparklineWidget] = None
        
        # Initialize psutil process if available
        if PSUTIL_AVAILABLE:
            try:
                self.process = psutil.Process()
            except Exception as e:
                self._update_status(f"⚠️ Memory monitoring error: {str(e)}")
        else:
            self._update_status("⚠️ Memory monitoring unavailable (psutil not installed)")
    
    def set_sparkline_widget(self, widget: SparklineWidget) -> None:
        """Associate a sparkline widget for visual memory display"""
        self.sparkline_widget = widget
    
    def start_monitoring(self) -> None:
        """Start the memory monitoring loop"""
        if not PSUTIL_AVAILABLE or not self.process:
            self._update_status("Memory monitoring not available")
            return
        
        self.is_active = True
        self._monitoring_loop()
    
    def stop_monitoring(self) -> None:
        """Stop the memory monitoring loop"""
        self.is_active = False
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop - collects data and schedules next update"""
        if not self.is_active:
            return
        
        try:
            # Get current memory usage
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            
            # Update sparkline if available
            if self.sparkline_widget:
                self.sparkline_widget.add_data_point(memory_mb)
            
            # Generate and send status update
            status_text = self._build_status_text(memory_mb)
            self._update_status(status_text)
            
        except Exception as e:
            self._update_status(f"Memory monitoring error: {str(e)}")
        
        # Schedule next update
        if self.scheduler_callback:
            self.scheduler_callback(self.update_interval_ms, self._monitoring_loop)
    
    def _build_status_text(self, memory_mb: float) -> str:
        """Build formatted status text with icon, value, and trend"""
        if not self.sparkline_widget:
            return f"📊 {memory_mb:.1f}MB"
        
        # Get status icon based on thresholds
        icon = self._get_status_icon(memory_mb)
        
        # Get trend indicator
        trend = self._get_trend_indicator()
        
        # Build status text
        status_text = f"{icon} {memory_mb:.1f}MB {trend}"
        
        # Add baseline if available
        if self.sparkline_widget.yellow_threshold > 0:
            status_text += f" (Baseline: {self.sparkline_widget.baseline:.0f}MB)"
        
        return status_text
    
    def _get_status_icon(self, memory_mb: float) -> str:
        """Get appropriate status icon based on memory usage and thresholds"""
        if not self.sparkline_widget:
            return '📊'
        
        if (hasattr(self.sparkline_widget, 'red_threshold') and 
            memory_mb > self.sparkline_widget.red_threshold):
            return '🚨'
        elif (hasattr(self.sparkline_widget, 'yellow_threshold') and 
              memory_mb > self.sparkline_widget.yellow_threshold):
            return '⚠️'
        else:
            return '📊'
    
    def _get_trend_indicator(self) -> str:
        """Calculate trend indicator from recent data points"""
        if not self.sparkline_widget or len(self.sparkline_widget.data) < 6:
            return '→'
        
        # Compare recent vs older data points
        recent = list(self.sparkline_widget.data)[-3:]
        older = list(self.sparkline_widget.data)[-6:-3]
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        
        if recent_avg > older_avg * 1.1:
            return '↗'
        elif recent_avg < older_avg * 0.9:
            return '↘'
        else:
            return '→'
    
    def _update_status(self, status_text: str) -> None:
        """Send status update via callback if available"""
        if self.status_callback:
            self.status_callback(status_text)
    
    @property
    def is_available(self) -> bool:
        """Check if memory monitoring is available"""
        return PSUTIL_AVAILABLE and self.process is not None