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

from i_vision_prototype_app import iVisionPrototypeApp

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