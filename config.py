"""Configuration constants and paths for the iVision Prototype application."""
from pathlib import Path

# Image paths
IMAGE_PATH = "./background/anastasius-8DkDA67JAIs-unsplash.jpg"
CAPTURE_DIR = Path("./captures")
CAPTURE_DIR.mkdir(exist_ok=True)

# UI Constants
CANVAS_WIDTH = 1000
CANVAS_HEIGHT = 520

# Lens defaults
DEFAULT_IPD = 240
DEFAULT_LENS_W_RATIO = 0.30
DEFAULT_LENS_H_RATIO = 0.56
DEFAULT_BRIDGE_MIN = 18

# Colors
COLORS = {
    'rim': (18, 18, 18, 255),
    'glass_tint': (0, 150, 255, 30),
    'hud_text': "lime",
    'background': "#111111",
    'panel_bg': "#0e2410",
    'panel_text': "#9aff9a"
}

"""
# Different lens tint options:
'glass_tint': (0, 255, 0, 36),    # Green tint (AR-style)
'glass_tint': (0, 150, 255, 30),  # Blue tint 
'glass_tint': (255, 255, 255, 20), # Clear/white tint
'glass_tint': (255, 200, 0, 40),   # Amber tint (sunglasses-style)
"""
