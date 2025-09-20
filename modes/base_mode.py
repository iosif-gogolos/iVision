"""Base class for application modes."""
from abc import ABC, abstractmethod


class BaseMode(ABC):
    """Abstract base class for application modes."""
    
    def __init__(self, app):
        self.app = app
        self.canvas = app.canvas
        self.items = []
        
    @abstractmethod
    def activate(self):
        """Activate this mode."""
        pass
        
    @abstractmethod
    def deactivate(self):
        """Deactivate this mode."""
        pass
        
    def clear_items(self):
        """Clear all mode-specific canvas items."""
        for item in self.items:
            self.canvas.delete(item)
        self.items = []