"""Image processing utilities for the iVision application"""
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from pathlib import Path
from config import IMAGE_PATH

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except:
    CV2_AVAILABLE = False
    cv2 = None
    np = None


def load_background_image():
    """Load and return the background iamge"""
    if not Path(IMAGE_PATH).exists():
        bg = Image.new("RGB", (1200, 600), (100, 120, 130))
        d = ImageDraw.Draw(bg)
        d.text((20,20), "Background image not found at:\n" + IMAGE_PATH, fill=(255,255,255))
        return bg
    return Image.open(IMAGE_PATH).convert("RGB")

def detect_damage_edges(pil_img):
    """Apply edge detection to highlight potential damage areas."""
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