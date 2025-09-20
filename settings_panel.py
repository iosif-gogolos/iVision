"""Settings panel component for the iVision application."""
import tkinter as tk
from config import COLORS


class SettingsPanel:
    """Manages the settings panel overlay."""
    
    def __init__(self, app):
        self.app = app
        self.panel = None
        self.variables = {}
        
    def toggle(self):
        """Toggle settings panel visibility."""
        if self.panel and self.panel.winfo_exists():
            self.panel.destroy()
            self.panel = None
            return

        self._create_panel()
        
    def _create_panel(self):
        """Create the settings panel."""
        # Panel dimensions (centered in the "glasses")
        pw, ph = 360, 200
        px = (self.app.canvas_w - pw) // 2
        py = int(self.app.canvas_h * 0.50) - ph // 2

        self.panel = tk.Frame(self.app.canvas, bg=COLORS['panel_bg'], bd=2, relief="ridge")
        self.panel.place(x=px, y=py, width=pw, height=ph)

        tk.Label(self.panel, text="Settings", fg=COLORS['panel_text'], bg=COLORS['panel_bg'],
                font=("Helvetica", 14, "bold")).pack(pady=(8, 6))

        self._create_controls()
        
        tk.Button(self.panel, text="Close", command=self.toggle).pack(pady=6)

    def _create_controls(self):
        """Create control widgets."""
        # IPD control
        row = tk.Frame(self.panel, bg=COLORS['panel_bg'])
        row.pack(fill="x", padx=10, pady=4)
        tk.Label(row, text="IPD", fg="white", bg=COLORS['panel_bg'], width=8).pack(side="left")
        self.variables['ipd'] = tk.IntVar(value=self.app.lens_params['ipd'])
        tk.Scale(row, from_=160, to=320, orient="horizontal", showvalue=True,
                variable=self.variables['ipd'], command=lambda v: self.app.update_lens_params(),
                length=220).pack(side="left")

        # Lens width control
        row2 = tk.Frame(self.panel, bg=COLORS['panel_bg'])
        row2.pack(fill="x", padx=10, pady=4)
        tk.Label(row2, text="Lens W", fg="white", bg=COLORS['panel_bg'], width=8).pack(side="left")
        self.variables['lens_w'] = tk.DoubleVar(value=self.app.lens_params['lens_w_ratio'])
        tk.Scale(row2, from_=0.22, to=0.36, resolution=0.01, orient="horizontal",
                variable=self.variables['lens_w'], command=lambda v: self.app.update_lens_params(),
                length=220).pack(side="left")

        # Lens height control
        row3 = tk.Frame(self.panel, bg=COLORS['panel_bg'])
        row3.pack(fill="x", padx=10, pady=4)
        tk.Label(row3, text="Lens H", fg="white", bg=COLORS['panel_bg'], width=8).pack(side="left")
        self.variables['lens_h'] = tk.DoubleVar(value=self.app.lens_params['lens_h_ratio'])
        tk.Scale(row3, from_=0.45, to=0.65, resolution=0.01, orient="horizontal",
                variable=self.variables['lens_h'], command=lambda v: self.app.update_lens_params(),
                length=220).pack(side="left")