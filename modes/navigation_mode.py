"""Navigation mode implementation."""
from .base_mode import BaseMode
from config import COLORS


class NavigationMode(BaseMode):
    """Handles navigation display and routing."""
    
    def activate(self):
        """Activate navigation mode."""
        self.clear_items()
        self.draw_navigation_overlay(direction="right", distance="600 ft", eta="23 mins")
        
    def deactivate(self):
        """Deactivate navigation mode."""
        self.clear_items()
        
    def draw_navigation_overlay(self, direction="right", distance="600 ft", eta="23 mins"):
        """Draw navigation overlay on the canvas."""
        lx, rx = self.app.get_lens_geometry()
        cx = (lx[2] + rx[0]) // 2  # middle gap between lenses
        cy = int((lx[1] + lx[3]) / 2)  # vertical center of lenses
        
        card_w, card_h = 320, 140
        card = self.canvas.create_rectangle(cx-card_w//2, cy-card_h//2,
                                           cx+card_w//2, cy+card_h//2,
                                           outline=COLORS['hud_text'], width=2)
        self.items.append(card)

        arrow_txt = "→" if direction == "right" else "←" if direction == "left" else "↑"
        arrow = self.canvas.create_text(cx-80, cy, text=arrow_txt, fill=COLORS['hud_text'],
                                       font=("Helvetica", 48, "bold"))
        self.items.append(arrow)

        t1 = self.canvas.create_text(cx+40, cy-18, text=distance, fill=COLORS['hud_text'],
                                    font=("Helvetica", 22, "bold"))
        t2 = self.canvas.create_text(cx+40, cy+18, text=eta, fill=COLORS['hud_text'],
                                    font=("Helvetica", 16))
        self.items.extend([t1, t2])

        # Update HUD navigation text
        self.app.hud_manager.update_navigation(f"{eta} {arrow_txt}")