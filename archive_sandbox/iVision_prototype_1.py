import os, sys, json, math, time
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageOps
import threading

try:
    import customtkinter as ctk
    TK_FRAME = "custom"
except Exception as e:
    import tkinter as tk
    from tkinter import ttk
    ctk = None 
    tk = tk
    TK_FRAME = "tk"

try:
    import cv2
    CV2_AVAILABLE = True
except Exception:
    CV2_AVAILABLE = False

try:
    import numpy as np
except Exception:
    np = None

IMAGE_PATH = "''' + IMAGE_PATH + '''"
CAPTURE_DIR = Path("./captures")
CAPTURE_DIR.mkdir(exist_ok=True)

if not Path(IMAGE_PATH).exists():
    bg = Image.new("RGB", (1200, 600), (100,120,130))
    d = ImageDraw.Draw(bg)
    d.text((20,20), "Background image not found at:\\n"+IMAGE_PATH, fill(255, 255,255))

class iVisionPrototypeApp:
    def __init__(self, root, using_custom=False):
        self.using_custom = using_custom
        self.root = root
        self.root.title

def run_app():
    if TK_FRAME=='custom':
        root = ctk.CTk()
        app = iVisionPrototypeApp(root, using_custom=True)
        app.update_hud()
        root.geometry("1040x780")
    else:
        root = tk.Tk()
        app = iVisionPrototypeApp(root, using_custom=False)
        app.update_hud()
        root.geometry("1040x780")
        app.mainloop()


if __name__ == '__main__':
    run_app()