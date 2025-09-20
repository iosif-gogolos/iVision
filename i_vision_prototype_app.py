# Requires: Pillow, opencv-python (optional), customtkinter (optional)
#   pip install pillow opencv-python customtkinter

import os, sys, json, time
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw

# --- UI framework: try customtkinter, fallback to tkinter ---
try:
    import customtkinter as ctk
    TK_FRAME = "custom"
    import tkinter as tk
    from tkinter import messagebox
except Exception:
    TK_FRAME = "tk"
    import tkinter as tk
    from tkinter import ttk, messagebox

from config import *
from settings_panel import SettingsPanel
from image_processing import load_background_image, detect_damage_edges
from ui_components import GlassesOverlay, HUDManager
from modes.navigation_mode import NavigationMode
from modes.carscan_mode import CarScanMode


class iVisionPrototypeApp:
    """Main application class for the iVision AR prototype."""
    
    def __init__(self, root, using_custom=False):
        self.using_custom = using_custom
        self.root = root
        self.root.title("iVision - Prototype")
        
        # Core components
        self.canvas_w, self.canvas_h = CANVAS_WIDTH, CANVAS_HEIGHT
        self.bg_resized = load_background_image().resize((self.canvas_w, self.canvas_h), Image.LANCZOS)
        self.glasses_overlay = GlassesOverlay((self.canvas_w, self.canvas_h))
        
        # Lens parameters
        self.lens_params = {
            'ipd': DEFAULT_IPD,
            'lens_w_ratio': DEFAULT_LENS_W_RATIO,
            'lens_h_ratio': DEFAULT_LENS_H_RATIO
        }
        
        # State
        self.mode = "menu"
        self.captures = []
        self.knob_bbox = None
        
        # Initialize components
        self.settings_panel = SettingsPanel(self)

        self.create_ui()
        self.update_overlay()
        
        # Position HUD items after overlay is ready
        self.hud_manager.position_items(self.get_lens_geometry())
        
        # Initialize modes
        self.modes = {
            'navigation': NavigationMode(self),
            'carscan': CarScanMode(self)
        }

    def create_ui(self):
        """Create the main UI components."""
        # Main frame
        if self.using_custom:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            self.frame = ctk.CTkFrame(self.root, corner_radius=0)
        else:
            self.frame = tk.Frame(self.root, bg=COLORS['background'])
        self.frame.pack(fill="both", expand=True)

        # Top status bar
        self._create_status_bar()
        
        # Canvas
        self._create_canvas()
        
        # Bottom controls
        self._create_controls()

    def _create_status_bar(self):
        """Create the top status bar."""
        top = (ctk.CTkFrame(self.frame, height=40, fg_color="#0f0f0f")
               if self.using_custom else tk.Frame(self.frame, height=40, bg="#0f0f0f"))
        top.pack(fill="x", side="top")
        
        if self.using_custom:
            self.status_label = ctk.CTkLabel(top, text="Battery: 86%  |  Mode: Menu", anchor="w")
        else:
            self.status_label = tk.Label(top, text="Battery: 86%  |  Mode: Menu", 
                                       fg="white", bg="#0f0f0f", anchor="w")
        self.status_label.pack(side="left", padx=10)

    def _create_canvas(self):
        """Create the main canvas."""
        self.canvas = (ctk.CTkCanvas(self.frame, width=self.canvas_w, height=self.canvas_h)
                      if self.using_custom else
                      tk.Canvas(self.frame, width=self.canvas_w, height=self.canvas_h, 
                               bg="black", highlightthickness=0))
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        
        # Initialize HUD
        self.hud_manager = HUDManager(self.canvas, self.canvas_w, self.canvas_h)
        self.hud_manager.create_items()
        
        # Start HUD updates
        self.root.after(1000, self._update_hud_timer)

    def _create_controls(self):
        """Create bottom control buttons."""
        ctrl = tk.Frame(self.frame, height=90, bg="#0f0f0f")
        ctrl.pack(fill="x", side="bottom", pady=6)
        
        tk.Button(ctrl, text="Menu", command=self.show_menu, width=12).pack(side="left", padx=6)
        tk.Button(ctrl, text="CarScan", command=self.open_carscan, width=14).pack(side="left", padx=6)
        tk.Button(ctrl, text="Navigation", command=self.open_navigation, width=16).pack(side="left", padx=6)
        tk.Button(ctrl, text="Capture Frame", command=self.capture_frame, width=16).pack(side="right", padx=6)
        tk.Button(ctrl, text="Crown", command=self.settings_panel.toggle, width=10).pack(side="right", padx=6)

    def update_overlay(self):
        """Update the glasses overlay with current parameters."""
        self.overlay_img, self.knob_bbox = self.glasses_overlay.generate(
            ipd_px=self.lens_params['ipd'],
            lens_w_ratio=self.lens_params['lens_w_ratio'],
            lens_h_ratio=self.lens_params['lens_h_ratio']
        )
        self._redraw_base()

    def update_lens_params(self):
        """Update lens parameters from settings panel."""
        if hasattr(self.settings_panel, 'variables'):
            self.lens_params['ipd'] = int(self.settings_panel.variables['ipd'].get())
            self.lens_params['lens_w_ratio'] = float(self.settings_panel.variables['lens_w'].get())
            self.lens_params['lens_h_ratio'] = float(self.settings_panel.variables['lens_h'].get())
            self.update_overlay()
            self.hud_manager.position_items(self.get_lens_geometry())

    def get_lens_geometry(self):
        """Get current lens geometry for positioning calculations."""
        w, h = self.canvas_w, self.canvas_h
        cx = w // 2
        cy = int(h * 0.53)
        lw = int(w * self.lens_params['lens_w_ratio'])
        lh = int(h * self.lens_params['lens_h_ratio'])
        ipd_eff = max(self.lens_params['ipd'], lw + DEFAULT_BRIDGE_MIN)
        
        lx_c = (cx - ipd_eff // 2, cy)
        rx_c = (cx + ipd_eff // 2, cy)
        
        def bbox(c):
            x, y = c
            return [x - lw//2, y - lh//2, x + lw//2, y + lh//2]
            
        return bbox(lx_c), bbox(rx_c)

    def _redraw_base(self):
        """Redraw the base composite image."""
        comp = Image.alpha_composite(self.bg_resized.convert("RGBA"), self.overlay_img)
        self.composite_img = comp
        self.tk_img = ImageTk.PhotoImage(self.composite_img)
        
        if hasattr(self, "canvas_img_id"):
            self.canvas.itemconfigure(self.canvas_img_id, image=self.tk_img)
        else:
            self.canvas_img_id = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

    def _on_canvas_click(self, event):
        """Handle canvas clicks for digital crown interaction."""
        if self.knob_bbox:
            x1, y1, x2, y2 = self.knob_bbox
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.settings_panel.toggle()

    def _update_hud_timer(self):
        """Update HUD elements periodically."""
        self.hud_manager.update_time()
        self.root.after(1000, self._update_hud_timer)

    # Mode switching methods
    def show_menu(self):
        """Show main menu."""
        self._switch_mode("menu")
        # Clear any mode overlays when returning to menu
        for mode in self.modes.values():
            mode.deactivate()

    def open_navigation(self):
        """Open navigation mode."""
        self._switch_mode("navigation")
        self.modes['navigation'].activate()

    def open_carscan(self):
        """Open car scan mode."""
        self._switch_mode("carscan")
        self.modes['carscan'].activate()

    def _switch_mode(self, mode_name):
        """Switch to a different mode."""
        # Deactivate current mode
        if self.mode in self.modes:
            self.modes[self.mode].deactivate()
            
        self.mode = mode_name
        self.status_label.config(text=f"Battery: 86%  |  Mode: {mode_name.title()}")

    def capture_frame(self):
        """Capture current frame with metadata."""
        comp = Image.alpha_composite(self.bg_resized.convert("RGBA"), self.overlay_img)
        draw = ImageDraw.Draw(comp)
        ts = int(time.time())
        
        meta = {
            "timestamp": ts,
            "mode": self.mode,
            "lens_params": self.lens_params.copy()
        }

        # Add mode-specific metadata
        if self.mode == "carscan" and 'carscan' in self.modes:
            carscan_mode = self.modes['carscan']
            meta["guide_step"] = carscan_mode.guide_step
            target_pos = carscan_mode.get_current_target_position()
            if target_pos:
                meta["guide_center"] = target_pos
                # Draw highlight on capture
                mx, my = target_pos
                draw.ellipse([mx - 30, my - 30, mx + 30, my + 30], 
                           outline=(0, 255, 0, 255), width=6)

        # Save files
        img_fn = CAPTURE_DIR / f"capture_{ts}.png"
        comp.convert("RGB").save(img_fn)
        
        det = detect_damage_edges(comp.convert("RGB"))
        det_fn = CAPTURE_DIR / f"capture_{ts}_det.png"
        det.convert("RGB").save(det_fn)
        
        with open(CAPTURE_DIR / f"capture_{ts}.json", "w") as f:
            json.dump(meta, f, indent=2)

        messagebox.showinfo("Capture saved", f"Saved {img_fn.name}\nDamage overlay: {det_fn.name}")
        self.refresh_canvas_view()

    def refresh_canvas_view(self):
        """Refresh the canvas view maintaining overlays."""
        self._redraw_base()
        self.hud_manager.position_items(self.get_lens_geometry())
        
        # Refresh active mode overlays
        if self.mode in self.modes:
            self.modes[self.mode].activate()
            
        if self.settings_panel.panel and self.settings_panel.panel.winfo_exists():
            self.settings_panel.panel.lift()