"""CarScan mode implementation."""
from .base_mode import BaseMode
from config import COLORS


class CarScanMode(BaseMode):
    """Handles car damage detection and guidance."""
    
    def __init__(self, app):
        super().__init__(app)
        self.guide_step = 0
        
    def activate(self):
        """Activate car scan mode."""
        self.clear_items()
        self.guide_step = 0
        self.show_guidance_overlay(self.guide_step)
        
    def deactivate(self):
        """Deactivate car scan mode."""
        self.clear_items()
        
    def show_guidance_overlay(self, step=0):
        """Show guidance overlay for car scanning."""
        self.clear_items()
        
        steps = [
            (0.35, 0.35), (0.65, 0.35),
            (0.20, 0.60), (0.50, 0.60),
            (0.80, 0.60), (0.35, 0.80),
            (0.65, 0.80), (0.50, 0.50)
        ]
        
        x_rel, y_rel = steps[step % len(steps)]
        x = int(self.app.canvas_w * x_rel)
        y = int(self.app.canvas_h * y_rel)
        
        ring = self.canvas.create_oval(x - 40, y - 40, x + 40, y + 40, 
                                      outline=COLORS['hud_text'], width=3)
        arrow = self.canvas.create_polygon(x, y - 70, x - 10, y - 35, x + 10, y - 35, 
                                         fill=COLORS['hud_text'])
        txt = self.canvas.create_text(x, y + 60, text=f"Target {step + 1}", 
                                     fill=COLORS['hud_text'], font=("Helvetica", 12, "bold"))
        
        self.items.extend([ring, arrow, txt])
        
    def next_step(self):
        """Move to next guidance step."""
        self.guide_step += 1
        self.show_guidance_overlay(self.guide_step)
        
    def get_current_target_position(self):
        """Get the current target position for capture metadata."""
        if self.items:
            coords = self.canvas.coords(self.items[0])  # Ring coordinates
            mx = int((coords[0] + coords[2]) / 2)
            my = int((coords[1] + coords[3]) / 2)
            return [mx, my]
        return None