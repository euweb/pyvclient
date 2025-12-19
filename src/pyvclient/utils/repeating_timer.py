"""
Repeating timer utility for periodic updates.
"""
import logging
import threading
from typing import List, Callable

logger = logging.getLogger(__name__)


class RepeatingTimer:
    """Timer that repeatedly executes callbacks at specified interval."""
    
    def __init__(self, interval: int):
        """
        Initialize repeating timer.
        
        Args:
            interval: Interval in seconds between executions
        """
        self.interval = interval
        self.callbacks: List[Callable] = []
        self.timer: threading.Timer = None
        self.running = False
        
    def add_callback(self, callback: Callable):
        """Add callback function to be executed."""
        self.callbacks.append(callback)
        if not self.running:
            self.start()
    
    def start(self):
        """Start the repeating timer."""
        if not self.running:
            self.running = True
            self._schedule()
            logger.debug(f"Started repeating timer with interval {self.interval}s")
    
    def stop(self):
        """Stop the repeating timer."""
        self.running = False
        if self.timer:
            self.timer.cancel()
            logger.debug(f"Stopped repeating timer")
    
    def _schedule(self):
        """Schedule next execution."""
        if self.running:
            self.timer = threading.Timer(self.interval, self._execute)
            self.timer.daemon = True
            self.timer.start()
    
    def _execute(self):
        """Execute all callbacks and reschedule."""
        for callback in self.callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error executing timer callback: {e}", exc_info=True)
        
        # Schedule next execution
        if self.running:
            self._schedule()
