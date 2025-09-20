"""Configuration constants and paths for the iVision Prototype application."""
from pathlib import Path

# Image paths
IMAGE_PATH = "./background/anastasius-8DkDA67JAIs-unsplash.jpg"
CAPTURE_DIR = Path("./captures")
CAPTURE_DIR.mkdir(exist_ok=True)

# UI COnstants
CANVAS_WIDTH = 1000
CANVAS_HEIGHT = 520

# Lens defaults
DEFAULT_IPD = 240
DEFAULT_LENS_W_RATIO = 0.30
DEFAULT_LENTS_H_RATIO = 0.56
DEFAULT_BRIDGE_MIN = 18

# Colors
COLORS = {
    'rim': (18,18,18,255),
    'glass_tint':("lime"),
    'hud_text':"lime",
    'background':"#111111",
    'panel_bg': "#0e2410",
    'panel_text':"#9aff9a"
}

