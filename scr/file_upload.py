import tkinter as tk
from tkinter import filedialog

def uploadFile():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(title="Select a file", filetypes=[("PNG files", "*.png")])
    root.destroy()

    if file_path == "":
        return None
    return file_path