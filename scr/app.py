import customtkinter as ctk


from scr.javaJDK_downloader import javaJDKUpdateAvailable
from scr.ui_functions import *
from scr.ui_elements import ElementManager


class App:
    def __init__(self, root):
        self.font = ctk.CTkFont(family="resouces/font/Aldrich-Regular.ttf", size=24)

        self.root = root
        self.root.geometry("862x519")
        self.root.title("Zenith")
        self.root.resizable(False, False)
        self.root.iconbitmap('resources/icon.ico')
        self.root.configure(bg="#242424")
        ctk.CTkFont(family="Aldrich-Regular.ttf", size=24)

        self.page = ctk.CTkFrame(self.root, fg_color="transparent")
        ElementManager.setSurface(self.page, self.root)
        
        if javaJDKUpdateAvailable():
            ElementManager.loadPage("downloadJDK/downloadJDK")
        else:
            ElementManager.loadPage("home/home")

root = ctk.CTk()
app = App(root)

app.root.after(16, ElementManager.checks)

root.mainloop()