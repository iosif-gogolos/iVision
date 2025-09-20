# Save this script as ar_prototype.py and run:
#   python ar_prototype.py
# Requires: Pillow, opencv-python (optional), customtkinter (optional)
#   pip install pillow opencv-python customtkinter

import os, sys, json, time
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageOps

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

# --- Optional OpenCV / NumPy ---
try:
    import cv2
    CV2_AVAILABLE = True
except Exception:
    CV2_AVAILABLE = False
try:
    import numpy as np
except Exception:
    np = None

# --- Config / assets ---
#IMAGE_PATH = "./background/josh-hild-cvi752mY6eA-unsplash.jpg" # dark city
#IMAGE_PATH = "./background/detait-A1_rJmm6hz8-unsplash.jpg"
IMAGE_PATH = "./background/anastasius-8DkDA67JAIs-unsplash.jpg"

CAPTURE_DIR = Path("./captures")
CAPTURE_DIR.mkdir(exist_ok=True)

# Load background
if not Path(IMAGE_PATH).exists():
    bg = Image.new("RGB", (1200, 600), (100, 120, 130))
    d = ImageDraw.Draw(bg)
    d.text((20, 20), "Background image not found at:\n" + IMAGE_PATH, fill=(255, 255, 255))
else:
    bg = Image.open(IMAGE_PATH).convert("RGB")

# ---------- Helpers ----------

def detect_damage_edges(pil_img):
    if not CV2_AVAILABLE or np is None:
        img = pil_img.convert("L").filter(ImageFilter.FIND_EDGES)
        colored = ImageOps.colorize(img, black="black", white="lime")
        return Image.blend(pil_img.convert("RGBA"), colored.convert("RGBA"), alpha=0.35)
    arr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    g = clahe.apply(gray)
    edges = cv2.Canny(g, 60, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    edges = cv2.dilate(edges, kernel, iterations=1)
    overlay = arr.copy()
    overlay[edges > 0] = (0, 255, 0)
    blended = cv2.addWeighted(arr, 0.7, overlay, 0.3, 0)
    return Image.fromarray(cv2.cvtColor(blended, cv2.COLOR_BGR2RGB)).convert("RGBA")

def make_glasses_overlay_binocular_realistic(
    size=(1200, 600),
    rim_color=(18, 18, 18, 255),
    glass_tint=(0, 255, 0, 36),
    ipd_px=240,
    lens_w_ratio=0.30,
    lens_h_ratio=0.56,
    bridge_min=18,
    lower_bar_h_ratio=0.12
    
    
):
    """
    Επιστρέφει (overlay_rgba, knob_bbox) ώστε να μπορούμε να κάνουμε hit-test στη ροδέλα.
    knob_bbox: (x1,y1,x2,y2) σε συντεταγμένες canvas.
    """
    w, h = size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Κέντρο & διαστάσεις
    cx = w // 2
    cy = int(h * 0.53)
    lw = int(w * lens_w_ratio)
    lh = int(h * lens_h_ratio)

    # Auto-fit IPD (να μην τέμνονται)
    ipd_eff = max(ipd_px, lw + bridge_min)

    lx_c = (cx - ipd_eff // 2, cy)
    rx_c = (cx + ipd_eff // 2, cy)

    def lens_bbox(c):
        x, y = c
        return [x - lw//2, y - lh//2, x + lw//2, y + lh//2]

    rim_w = 10

    # Drop shadow (διακριτικό)
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    for off in range(2, 8, 2):
        sd.ellipse([lens_bbox(lx_c)[0]+off, lens_bbox(lx_c)[1]+off,
                    lens_bbox(lx_c)[2]+off, lens_bbox(lx_c)[3]+off], outline=(0,0,0,50))
        sd.ellipse([lens_bbox(rx_c)[0]+off, lens_bbox(rx_c)[1]+off,
                    lens_bbox(rx_c)[2]+off, lens_bbox(rx_c)[3]+off], outline=(0,0,0,50))
    overlay = Image.alpha_composite(shadow, overlay)
    draw = ImageDraw.Draw(overlay)

    # Rims
    draw.ellipse(lens_bbox(lx_c), outline=rim_color, width=rim_w)
    draw.ellipse(lens_bbox(rx_c), outline=rim_color, width=rim_w)

    # Bridge
    bx1 = lx_c[0] + lw//2
    bx2 = rx_c[0] - lw//2
    by  = cy - lh//8
    if bx2 > bx1:
        draw.rectangle([bx1, by, bx2, by + max(4, bridge_min//2)], fill=rim_color)
    else:
        draw.line([(lx_c[0] + lw // 2, cy), (rx_c[0] - lw // 2, cy)], fill=rim_color, width=4)

    # Temple arms (βραχίονες)
    arm_h = int(lh*0.18)
    # αριστερός
    draw.rounded_rectangle([int(w*0.03), cy - arm_h//2, lx_c[0] - lw//2 + 10, cy + arm_h//2],
                           radius=arm_h//2, fill=(22,22,22,255))
    # δεξιός
    right_arm_box = [rx_c[0] + lw//2 - 10, cy - arm_h//2, int(w*0.97), cy + arm_h//2]
    draw.rounded_rectangle(right_arm_box, radius=arm_h//2, fill=(22,22,22,255))

    # Digital crown (ροδέλα) στον δεξιό βραχίονα
    crown_r = arm_h//2 + 8
    crown_cx = right_arm_box[2] - crown_r - 6
    crown_cy = cy
    # σώμα
    draw.ellipse([crown_cx - crown_r, crown_cy - crown_r, crown_cx + crown_r, crown_cy + crown_r],
                 fill=(30,30,30,255), outline=(12,12,12,255), width=3)
    # ανάγλυφο δαχτυλίδι
    draw.ellipse([crown_cx - crown_r + 6, crown_cy - crown_r + 6,
                  crown_cx + crown_r - 6, crown_cy + crown_r - 6],
                 outline=(80,80,80,255), width=2)
    knob_bbox = (crown_cx - crown_r, crown_cy - crown_r, crown_cx + crown_r, crown_cy + crown_r)

    # Tint μέσα στους φακούς
    draw.ellipse(lens_bbox(lx_c), fill=glass_tint)
    draw.ellipse(lens_bbox(rx_c), fill=glass_tint)
    draw.ellipse(lens_bbox(lx_c), outline=rim_color, width=rim_w)
    draw.ellipse(lens_bbox(rx_c), outline=rim_color, width=rim_w)

    frame_margin = 20
    frame_box = [lx_c[0] - lw//2 - frame_margin,
                 cy - lh//2 - frame_margin,
                 rx_c[0] + lw//2 + frame_margin,
                 cy + lh//2 + frame_margin]
    draw.rounded_rectangle(frame_box, radius=40,
                           outline=(220,220,220,255), width=8, fill=(40,40,40,120))

    # --- Lens rims ---
    draw.ellipse(lens_bbox(lx_c), outline=(250,250,250,255), width=rim_w)
    draw.ellipse(lens_bbox(rx_c), outline=(250,250,250,255), width=rim_w)


    # Κάτω μπάρα (σαν «στέλεχος/τιμόνι»)
    bottom = int(h * 0.90)
    sb_top = bottom - int(h * lower_bar_h_ratio)
    sb_left = int(w * 0.18)
    sb_right = int(w * 0.82)
    draw.rectangle([sb_left, sb_top, sb_right, bottom+8], fill=(20, 20, 20, 255))

    return overlay, knob_bbox


# ---------- App ----------

class iVisionPrototypeApp:
    def __init__(self, root, using_custom=False):
        self.using_custom = using_custom
        self.root = root
        self.root.title("iVision - Prototype")
        self.guides = []
        self.nav_items = []
        self.settings_panel = None
        self.knob_bbox = None

        if using_custom:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            self.frame = ctk.CTkFrame(root, corner_radius=0)
        else:
            self.frame = tk.Frame(root, bg="#111111")
        self.frame.pack(fill="both", expand=True)

        self.canvas_w, self.canvas_h = 1000, 520
        self.bg_resized = bg.copy().resize((self.canvas_w, self.canvas_h), Image.LANCZOS)

        # φακοί – αρχικές παράμετροι
        self._ipd = 240
        self._lw_ratio = 0.30
        self._lh_ratio = 0.56
        self.overlay_img, self.knob_bbox = make_glasses_overlay_binocular_realistic(
            (self.canvas_w, self.canvas_h),
            ipd_px=self._ipd, lens_w_ratio=self._lw_ratio, lens_h_ratio=self._lh_ratio
        )

        self.mode = "menu"
        self.captures = []

        self.create_ui()

    def create_ui(self):
        # Top status
        top = (ctk.CTkFrame(self.frame, height=40, fg_color="#0f0f0f")
               if self.using_custom else tk.Frame(self.frame, height=40, bg="#0f0f0f"))
        top.pack(fill="x", side="top")
        if self.using_custom:
            self.status_label = ctk.CTkLabel(top, text="Battery: 86%  |  Mode: Menu", anchor="w")
        else:
            self.status_label = tk.Label(top, text="Battery: 86%  |  Mode: Menu", fg="white", bg="#0f0f0f", anchor="w")
        self.status_label.pack(side="left", padx=10)

        # Canvas
        self.canvas = (ctk.CTkCanvas(self.frame, width=self.canvas_w, height=self.canvas_h)
                       if self.using_custom else
                       tk.Canvas(self.frame, width=self.canvas_w, height=self.canvas_h, bg="black", highlightthickness=0))
        self.canvas.pack(pady=10)
        self._redraw_base()
        #self._position_hud()

        

        # HUD
        self.create_hud_items()
        
        # Capture click στο crown
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # Bottom controls
        ctrl = tk.Frame(self.frame, height=90, bg="#0f0f0f")
        ctrl.pack(fill="x", side="bottom", pady=6)
        tk.Button(ctrl, text="Menu", command=self.show_menu, width=12).pack(side="left", padx=6)
        tk.Button(ctrl, text="CarScan (open)", command=self.open_carscan, width=14).pack(side="left", padx=6)
        tk.Button(ctrl, text="Navigation (open)", command=self.open_navigation, width=16).pack(side="left", padx=6)
        tk.Button(ctrl, text="Capture Frame", command=self.capture_frame, width=16).pack(side="right", padx=6)
        tk.Button(ctrl, text="Crown", command=self.toggle_settings_panel, width=10).pack(side="right", padx=6)

    # ----- Base redraw -----
    def _redraw_base(self):
        comp = Image.alpha_composite(self.bg_resized.convert("RGBA"), self.overlay_img)
        self.composite_img = comp
        self.tk_img = ImageTk.PhotoImage(self.composite_img)
        if hasattr(self, "canvas_img_id"):
            self.canvas.itemconfigure(self.canvas_img_id, image=self.tk_img)
        else:
            self.canvas_img_id = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

    # ----- Settings panel (μέσα στο γυαλί) -----
    def toggle_settings_panel(self):
        if self.settings_panel and self.settings_panel.winfo_exists():
            self.settings_panel.destroy()
            self.settings_panel = None
            return

        # panel dimensions (στο κέντρο, μέσα στο «γυαλί»)
        pw, ph = 360, 200
        px = (self.canvas_w - pw)//2
        py = int(self.canvas_h*0.50) - ph//2

        self.settings_panel = tk.Frame(self.canvas, bg="#0e2410", bd=2, relief="ridge")
        self.settings_panel.place(x=px, y=py, width=pw, height=ph)

        tk.Label(self.settings_panel, text="Settings", fg="#9aff9a", bg="#0e2410",
                 font=("Helvetica", 14, "bold")).pack(pady=(8,6))

        row = tk.Frame(self.settings_panel, bg="#0e2410"); row.pack(fill="x", padx=10, pady=4)
        tk.Label(row, text="IPD", fg="white", bg="#0e2410", width=8).pack(side="left")
        self.ipd_var = tk.IntVar(value=self._ipd)
        tk.Scale(row, from_=160, to=320, orient="horizontal", showvalue=True,
                 variable=self.ipd_var, command=lambda v: self._on_params_change(),
                 length=220).pack(side="left")

        row2 = tk.Frame(self.settings_panel, bg="#0e2410"); row2.pack(fill="x", padx=10, pady=4)
        tk.Label(row2, text="Lens W", fg="white", bg="#0e2410", width=8).pack(side="left")
        self.lw_var = tk.DoubleVar(value=self._lw_ratio)
        tk.Scale(row2, from_=0.22, to=0.36, resolution=0.01, orient="horizontal",
                 variable=self.lw_var, command=lambda v: self._on_params_change(),
                 length=220).pack(side="left")

        row3 = tk.Frame(self.settings_panel, bg="#0e2410"); row3.pack(fill="x", padx=10, pady=4)
        tk.Label(row3, text="Lens H", fg="white", bg="#0e2410", width=8).pack(side="left")
        self.lh_var = tk.DoubleVar(value=self._lh_ratio)
        tk.Scale(row3, from_=0.45, to=0.65, resolution=0.01, orient="horizontal",
                 variable=self.lh_var, command=lambda v: self._on_params_change(),
                 length=220).pack(side="left")

        tk.Button(self.settings_panel, text="Close", command=self.toggle_settings_panel).pack(pady=6)

    def _on_canvas_click(self, event):
        # hit test της ροδέλας
        if self.knob_bbox:
            x1,y1,x2,y2 = self.knob_bbox
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.toggle_settings_panel()

    def _on_params_change(self):
        # ενημέρωσε overlay και redraw
        if hasattr(self, "ipd_var"):
            self._ipd = int(self.ipd_var.get())
            self._lw_ratio = float(self.lw_var.get())
            self._lh_ratio = float(self.lh_var.get())
            self.overlay_img, self.knob_bbox = make_glasses_overlay_binocular_realistic(
                (self.canvas_w, self.canvas_h),
                ipd_px=self._ipd, lens_w_ratio=self._lw_ratio, lens_h_ratio=self._lh_ratio
            )
            self._redraw_base()
            self._position_hud()
            # κράτησε HUD/overlays πάνω
            for item in (getattr(self, "hud_time", None), getattr(self, "hud_batt", None), getattr(self, "hud_nav", None)):
                if item: self.canvas.tag_raise(item)
            if self.settings_panel and self.settings_panel.winfo_exists():
                self.settings_panel.lift()

    # ----- Navigation -----
    def open_navigation(self):
        self.mode = "navigation"
        self.status_label.config(text="Battery: 86%  |  Mode: Navigation")
        self.clear_guides()
        self.draw_navigation_overlay(direction="right", distance="600 ft", eta="23 mins")

    def clear_guides(self):
        for g in getattr(self, "guides", []):
            self.canvas.delete(g)
        self.guides = []

    def draw_navigation_overlay(self, direction="right", distance="600 ft", eta="23 mins"):
        for it in getattr(self, "nav_items", []):
            self.canvas.delete(it)
        self.nav_items = []

        cx, cy = self.canvas_w//2, int(self.canvas_h*0.48)
        card_w, card_h = 320, 140
        card = self.canvas.create_rectangle(cx-card_w//2, cy-card_h//2,
                                            cx+card_w//2, cy+card_h//2,
                                            outline="lime", width=2)
        self.nav_items.append(card)

        arrow_txt = "→" if direction == "right" else "←" if direction == "left" else "↑"
        arrow = self.canvas.create_text(cx-80, cy, text=arrow_txt, fill="lime",
                                        font=("Helvetica", 48, "bold"))
        self.nav_items.append(arrow)

        t1 = self.canvas.create_text(cx+40, cy-18, text=distance, fill="lime",
                                     font=("Helvetica", 22, "bold"))
        t2 = self.canvas.create_text(cx+40, cy+18, text=eta, fill="lime",
                                     font=("Helvetica", 16))
        self.nav_items += [t1, t2]

        lx, rx = self._lens_geometry()
        cx = (lx[2] + rx[0]) // 2        # middle gap between lenses
        cy = int((lx[1] + lx[3]) / 2)    # vertical center of lenses
        card_w, card_h = 320, 140
        card = self.canvas.create_rectangle(cx-card_w//2, cy-card_h//2,
                                            cx+card_w//2, cy+card_h//2,
                                            outline="lime", width=2)
        
        #self.nav_items += [lane, suggest]
        self.canvas.itemconfigure(self.hud_nav, text=f"{eta} {arrow_txt}")

    # ----- HUD -----
    def create_hud_items(self):
        time_text = time.strftime("%H:%M")
        self.hud_time = self.canvas.create_text(0, 0, text=time_text, fill="lime",
                                                font=("Helvetica", 18, "bold"))
        self.hud_batt = self.canvas.create_text(0, 0, text="56% 🔋", fill="lime",
                                                font=("Helvetica", 14))
        self.hud_nav  = self.canvas.create_text(0, 0, text="23 mins →", fill="lime",
                                                font=("Helvetica", 14))
        self._position_hud()
        self.root.after(1000, self.update_hud)

    def update_hud(self):
        self.canvas.itemconfigure(self.hud_time, text=time.strftime("%H:%M"))
        self.root.after(1000, self.update_hud)

    # ----- Menu -----
    def show_menu(self):
        self.mode = "menu"
        self.status_label.config(text="Battery: 86%  |  Mode: Menu")
        if hasattr(self, "menu_window") and self.menu_window.winfo_exists():
            return
        self.menu_window = tk.Toplevel(self.root)
        self.menu_window.title("Main Menu (Grid)")
        self.menu_window.geometry("420x380")
        self.menu_window.configure(bg="#0b0b0b")
        icons = ["Phone", "Messages", "CarScan", "Music", "Maps", "Camera", "Settings", "Logs", "Help"]
        for i, name in enumerate(icons):
            r, c = divmod(i, 3)
            tk.Button(self.menu_window, text=name, width=12, height=4,
                      command=lambda n=name: self.menu_select(n)).grid(row=r, column=c, padx=10, pady=10)

    def menu_select(self, name):
        if name == "CarScan":
            self.open_carscan()
            if hasattr(self, "menu_window"):
                self.menu_window.destroy()
        else:
            messagebox.showinfo("App Launch", f"Launching {name} (mock)")

    # ----- CarScan -----
    def open_carscan(self):
        self.mode = "carscan"
        self.status_label.config(text="Battery: 86%  |  Mode: CarScan")
        self.guide_step = 0
        self.show_guidance_overlay(self.guide_step)
        self.guide_label = getattr(self, "guide_label", None)

    def show_guidance_overlay(self, step=0):
        for g in getattr(self, "guides", []):
            self.canvas.delete(g)
        self.guides = []
        steps = [
            (0.35, 0.35), (0.65, 0.35),
            (0.20, 0.60), (0.50, 0.60),
            (0.80, 0.60), (0.35, 0.80),
            (0.65, 0.80), (0.50, 0.50)
        ]
        x_rel, y_rel = steps[step % len(steps)]
        x = int(self.canvas_w * x_rel); y = int(self.canvas_h * y_rel)
        ring = self.canvas.create_oval(x - 40, y - 40, x + 40, y + 40, outline="lime", width=3)
        arrow = self.canvas.create_polygon(x, y - 70, x - 10, y - 35, x + 10, y - 35, fill="lime")
        txt = self.canvas.create_text(x, y + 60, text=f"Target {step + 1}", fill="lime",
                                      font=("Helvetica", 12, "bold"))
        self.guides.extend([ring, arrow, txt])

    def capture_frame(self):
        comp = Image.alpha_composite(self.bg_resized.convert("RGBA"), self.overlay_img)
        draw = ImageDraw.Draw(comp)
        ts = int(time.time())
        meta = {"timestamp": ts, "mode": self.mode, "guide_step": getattr(self, "guide_step", 0)}
        if self.mode == "carscan" and self.guides:
            x1, y1, x2, y2 = self.canvas.coords(self.guides[0])
            mx = int((x1 + x2) / 2); my = int((y1 + y2) / 2)
            draw.ellipse([mx - 30, my - 30, mx + 30, my + 30], outline=(0, 255, 0, 255), width=6)
            meta["guide_center"] = [mx, my]
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
        self._redraw_base()
        self._position_hud()
        # κράτα HUD/overlays πάνω
        for item in (getattr(self, "hud_time", None), getattr(self, "hud_batt", None), getattr(self, "hud_nav", None)):
            if item: self.canvas.tag_raise(item)
        for it in getattr(self, "nav_items", []):
            self.canvas.tag_raise(it)
        for g in getattr(self, "guides", []):
            self.canvas.tag_raise(g)
        if self.settings_panel and self.settings_panel.winfo_exists():
            self.settings_panel.lift()
    
    def _lens_geometry(self, bridge_min=18):
        """Return (lx_bbox, rx_bbox) for current parameters.
        Each box is [x1, y1, x2, y2] in canvas coords"""
        w, h = self.canvas_w, self.canvas_h
        cx = w // 2
        cy = int(h * 0.53)
        lw = int(w * self._lw_ratio)
        lh = int(h * self._lh_ratio)
        ipd_eff = max(self._ipd, lw + bridge_min)
        lx_c = (cx - ipd_eff // 2, cy)
        rx_c = (cx + ipd_eff // 2, cy)
        def bbox(c):
            x, y = c
            return [x - lw//2, y-lh//2, x + lw//2, y + lh//2]
        return bbox(lx_c), bbox(rx_c)

    def _position_hud(self):
        lx, rx = self._lens_geometry()
        # convenience
        def center(b): 
            return ((b[0]+b[2])//2, (b[1]+b[3])//2)
        lw = lx[2]-lx[0]; lh = lx[3]-lx[1]

        # Time: top-left of left lens
        time_x = lx[0] + int(0.08 * lw)
        time_y = lx[1] + int(0.12 * lh)
        self.canvas.coords(self.hud_time, time_x, time_y)

        # Battery: top-right of left lens
        batt_x = lx[2] - int(0.10 * lw)
        batt_y = lx[1] + int(0.12 * lh)
        self.canvas.coords(self.hud_batt, batt_x, batt_y)

        # Navigation: top-right of right lens
        nav_x = rx[2] - int(0.08 * (rx[2]-rx[0]))
        nav_y = rx[1] + int(0.12 * (rx[3]-rx[1]))
        self.canvas.coords(self.hud_nav, nav_x, nav_y)

        # keep them on top
        for item in (self.hud_time, self.hud_batt, self.hud_nav):
            self.canvas.tag_raise(item)

# --- Main loop ---
def run_app():
    if TK_FRAME == "custom":
        root = ctk.CTk()
    else:
        root = tk.Tk()
    app = iVisionPrototypeApp(root, using_custom=(TK_FRAME == "custom"))
    root.geometry("1040x780")
    root.mainloop()

if __name__ == "__main__":
    run_app()
