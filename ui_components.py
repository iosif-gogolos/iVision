"""UI components and overlay generation for the iVision application."""
from PIL import Image, ImageDraw
from config import COLORS, DEFAULT_BRIDGE_MIN
import time


class GlassesOverlay:
    """Generates realistic AR glasses overlay with adjustable parameters."""
    
    def __init__(self, size=(1000, 520)):
        self.size = size
        
    def generate(self, ipd_px=240, lens_w_ratio=0.30, lens_h_ratio=0.56, 
                 bridge_min=DEFAULT_BRIDGE_MIN, lower_bar_h_ratio=0.12):
        """Generate glasses overlay and return (overlay_rgba, knob_bbox)."""
        w, h = self.size
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Calculate lens positions
        cx, cy = w // 2, int(h * 0.53)
        lw, lh = int(w * lens_w_ratio), int(h * lens_h_ratio)
        ipd_eff = max(ipd_px, lw + bridge_min)
        
        lx_c = (cx - ipd_eff // 2, cy)
        rx_c = (cx + ipd_eff // 2, cy)

        def lens_bbox(c):
            x, y = c
            return [x - lw//2, y - lh//2, x + lw//2, y + lh//2]

        # Draw components - CHANGED ORDER: tint is now drawn AFTER frame
        self._draw_shadow(draw, lens_bbox, lx_c, rx_c)
        self._draw_bridge(draw, lx_c, rx_c, lw, lh, cy, bridge_min)
        knob_bbox = self._draw_arms(draw, w, h, lx_c, rx_c, lw, lh, cy)
        
        # Draw frame behind lenses
        self._draw_frame(draw, lx_c, rx_c, lw, lh, cy)
        
        # Draw tinted lenses on top
        self._draw_tint(draw, lens_bbox, lx_c, rx_c, lw)
        
        # Draw rims last so they're on top
        self._draw_rims(draw, lens_bbox, lx_c, rx_c, lw)
        
        self._draw_bottom_bar(draw, w, h, lower_bar_h_ratio)

        return overlay, knob_bbox

    def _draw_shadow(self, draw, lens_bbox, lx_c, rx_c):
        """Draw drop shadow for lenses."""
        for off in range(2, 8, 2):
            for center in [lx_c, rx_c]:
                bbox = lens_bbox(center)
                shadow_bbox = [bbox[0]+off, bbox[1]+off, bbox[2]+off, bbox[3]+off]
                draw.ellipse(shadow_bbox, outline=(0,0,0,50))

    def _draw_rims(self, draw, lens_bbox, lx_c, rx_c, rim_w=10):
        """Draw lens rims."""
        rim_color = (250,250,250,255)  # Use white rims
        for center in [lx_c, rx_c]:
            draw.ellipse(lens_bbox(center), outline=rim_color, width=rim_w)

    def _draw_bridge(self, draw, lx_c, rx_c, lw, lh, cy, bridge_min):
        """Draw bridge between lenses."""
        rim_color = COLORS['rim']
        bx1 = lx_c[0] + lw//2
        bx2 = rx_c[0] - lw//2
        by = cy - lh//8
        
        if bx2 > bx1:
            draw.rectangle([bx1, by, bx2, by + max(4, bridge_min//2)], fill=rim_color)
        else:
            draw.line([(lx_c[0] + lw // 2, cy), (rx_c[0] - lw // 2, cy)], 
                     fill=rim_color, width=4)

    def _draw_arms(self, draw, w, h, lx_c, rx_c, lw, lh, cy):
        """Draw temple arms and digital crown. Returns knob_bbox."""
        arm_h = int(lh * 0.18)
        
        # Left arm
        draw.rounded_rectangle([int(w*0.03), cy - arm_h//2, lx_c[0] - lw//2 + 10, cy + arm_h//2],
                              radius=arm_h//2, fill=(22,22,22,255))
        
        # Right arm
        right_arm_box = [rx_c[0] + lw//2 - 10, cy - arm_h//2, int(w*0.97), cy + arm_h//2]
        draw.rounded_rectangle(right_arm_box, radius=arm_h//2, fill=(22,22,22,255))

        # Digital crown
        crown_r = arm_h//2 + 8
        crown_cx = right_arm_box[2] - crown_r - 6
        crown_cy = cy
        
        draw.ellipse([crown_cx - crown_r, crown_cy - crown_r, crown_cx + crown_r, crown_cy + crown_r],
                    fill=(30,30,30,255), outline=(12,12,12,255), width=3)
        draw.ellipse([crown_cx - crown_r + 6, crown_cy - crown_r + 6,
                     crown_cx + crown_r - 6, crown_cy + crown_r - 6],
                    outline=(80,80,80,255), width=2)
        
        return (crown_cx - crown_r, crown_cy - crown_r, crown_cx + crown_r, crown_cy + crown_r)

    def _draw_frame(self, draw, lx_c, rx_c, lw, lh, cy):
        """Draw outer frame."""
        frame_margin = 20
        frame_box = [lx_c[0] - lw//2 - frame_margin,
                    cy - lh//2 - frame_margin,
                    rx_c[0] + lw//2 + frame_margin,
                    cy + lh//2 + frame_margin]
        draw.rounded_rectangle(frame_box, radius=40,
                              outline=(220,220,220,255), width=8, fill=(40,40,40,80))  # Reduced opacity

    def _draw_tint(self, draw, lens_bbox, lx_c, rx_c, rim_w=10):
        """Draw lens tint and final rims."""
        glass_tint = COLORS['glass_tint']
        
        for center in [lx_c, rx_c]:
            bbox = lens_bbox(center)
            draw.ellipse(bbox, fill=glass_tint)

    def _draw_bottom_bar(self, draw, w, h, lower_bar_h_ratio):
        """Draw bottom control bar."""
        bottom = int(h * 0.90)
        sb_top = bottom - int(h * lower_bar_h_ratio)
        sb_left = int(w * 0.18)
        sb_right = int(w * 0.82)
        draw.rectangle([sb_left, sb_top, sb_right, bottom+8], fill=(20, 20, 20, 255))


class HUDManager:
    """Manages heads-up display elements."""
    
    def __init__(self, canvas, canvas_w, canvas_h):
        self.canvas = canvas
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self.hud_items = {}
        
    def create_items(self):
        """Create HUD items."""
        time_text = time.strftime("%H:%M")
        self.hud_items['time'] = self.canvas.create_text(0, 0, text=time_text, fill=COLORS['hud_text'],
                                                         font=("Helvetica", 18, "bold"))
        self.hud_items['battery'] = self.canvas.create_text(0, 0, text="56% 🔋", fill=COLORS['hud_text'],
                                                           font=("Helvetica", 14))
        self.hud_items['navigation'] = self.canvas.create_text(0, 0, text="23 mins →", fill=COLORS['hud_text'],
                                                              font=("Helvetica", 14))
        
    def position_items(self, lens_geometry):
        """Position HUD items based on lens geometry."""
        lx, rx = lens_geometry
        lw, lh = lx[2]-lx[0], lx[3]-lx[1]

        # Time: top-left of left lens
        time_x = lx[0] + int(0.08 * lw)
        time_y = lx[1] + int(0.12 * lh)
        self.canvas.coords(self.hud_items['time'], time_x, time_y)

        # Battery: top-right of left lens
        batt_x = lx[2] - int(0.10 * lw)
        batt_y = lx[1] + int(0.12 * lh)
        self.canvas.coords(self.hud_items['battery'], batt_x, batt_y)

        # Navigation: top-right of right lens
        nav_x = rx[2] - int(0.08 * (rx[2]-rx[0]))
        nav_y = rx[1] + int(0.12 * (rx[3]-rx[1]))
        self.canvas.coords(self.hud_items['navigation'], nav_x, nav_y)

        self.raise_items()
        
    def raise_items(self):
        """Bring HUD items to front."""
        for item in self.hud_items.values():
            if item:
                self.canvas.tag_raise(item)
                
    def update_time(self):
        """Update time display."""
        if 'time' in self.hud_items:
            self.canvas.itemconfigure(self.hud_items['time'], text=time.strftime("%H:%M"))
            
    def update_navigation(self, text):
        """Update navigation display."""
        if 'navigation' in self.hud_items:
            self.canvas.itemconfigure(self.hud_items['navigation'], text=text)