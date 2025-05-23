import os
import json
import customtkinter as ctk
import tkinter.font as tkfont
import webbrowser
from PIL import ImageFont
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
from scr.server_manager import ServerManager, retriveMSJ
from scr.updater import Updater
from scr.app_data import AppData
from scr.ui_functions import *
from scr.settings import *

class ELEMENTMANAGER:
    def __init__(self):
        self.surface = None
        self.root = None
        self.frame_count = 0

        font_path = f'resources/font/Aldrich-Regular.ttf'
        ImageFont.truetype(font_path, 20)
        self.font = "Aldrich-Regular"

        self.elements = self.resetElements()
        self.data = {
            "zenith_version": CURRENT_VERSION,
            "versions": retriveMSJ("vanilla", "", True),
            "servers": ServerManager.retriveServers(),
            "selected_server": None,
            "current_data": None
        }
        self.theme = self.loadTheme()

    def setSurface(self, surface, root):
        self.surface = surface
        self.root = root

    def loadTheme(self):
        path = f'data/themes/{AppData.getAppData("theme")}.json'
        with open(path, "r") as f:
            data = json.load(f)
        return data

    def resetElements(self):
        return {"label": {}, "button": {}, "entry": {}, "optionmenu": {}, "list": {}, "switch": {}, "textbox": {}, "progressbar": {}, "segmentedbutton": {}, "slider": {}, "frame": {}, "image": {}, "linegraph": {}}

    def unpackText(self, text):
        parts = []
        current_part = ""
        in_brackets = False

        i = 0
        while i < len(text):
            char = text[i]

            if char == "$" and i + 1 < len(text) and text[i + 1] == "{":
                if current_part:
                    parts.append(current_part)
                    current_part = ""
                in_brackets = True
                i += 1
            elif char == "}" and in_brackets:
                current_part = f"%%%{current_part}"
                parts.append(current_part)
                current_part = ""
                in_brackets = False
            elif char == " " and not in_brackets:
                if current_part:
                    parts.append(current_part)
                    current_part = ""
            else:
                current_part += char

            i += 1

        if current_part:
            parts.append(current_part)

        output = ""
        for part in parts:
            if part.startswith("%%%"):
                output += f'{str(self.data[part[3:]])} '
            else:
                output += f'{part} '

        return output[:-1]

    def selectServer(self, name):
        self.data["selected_server"] = name
        self.loadPage("server/server")

    def newElement(self, surface, element, force_type=None, use_grid=False):
        surface.configure(fg_color="transparent")
        if "show" in element:
            if isinstance(element["show"], dict):
                if not eval(element["show"]["condition"]):
                    return
            else:
                if not element["show"]:
                    return
        side = "top" if "align" not in element else element["align"]
        etype = element["type"] if force_type is None else force_type

        if etype == "frame":
            width = element["width"]
            height = element["height"]
            frame_type = element["frame_type"] if "frame_type" in element else "standard"

            if frame_type == "standard":
                if "bg_color" in element:
                    frame = ctk.CTkFrame(surface, width=width, height=height, fg_color=element["bg_color"])
                else:
                    frame = ctk.CTkFrame(surface, width=width, height=height)
            elif frame_type == "scrollable":
                if "bg_color" in element:
                    frame = ctk.CTkScrollableFrame(surface, width=width, height=height, fg_color=element["bg_color"])
                else:
                    frame = ctk.CTkScrollableFrame(surface, width=width, height=height)

            for child in element["children"]:
                self.newElement(frame, child)

            if use_grid:
                frame.grid(column=element["grid"]["column"], row=element["grid"]["row"], sticky=element["grid"]["sticky"], padx=element["grid"]["padx"], pady=element["grid"]["pady"])
            else:
                frame.pack(pady=element["pad"], padx=element["padx"] if "padx" in element else 0, side=side)

            self.elements["frame"][element["id"]] = frame

        if etype == "label":
            font = ctk.CTkFont(family=self.font, size=element["size"], weight="bold")

            rawtext = element["text"]
            if isinstance(element["text"], dict):
                if element["text"]["type"] == "function":
                    text = f'{element["text"]["prefix"] if "prefix" in element["text"] else ""}{eval(element["text"]["function"])}{element["text"]["suffix"] if "suffix" in element["text"] else ""}'
            else:
                text = self.unpackText(element["text"])
            label = ctk.CTkLabel(surface, text=text, fg_color="transparent", font=font)
            if use_grid:
                label.grid(column=element["grid"]["column"], row=element["grid"]["row"], sticky=element["grid"]["sticky"], padx=element["grid"]["padx"], pady=element["grid"]["pady"])
            else:
                label.pack(pady=element["pad"], padx=element["padx"] if "padx" in element else 0, side=side)
            self.elements["label"][element["id"]] = {"obj": label, "rawtext": rawtext}

        if etype == "button":
            theme = self.theme["button"]
            f = element["function"]
            
            s = "normal"
            if "state" in element:
                if isinstance(element["state"], dict):
                    if eval(element["state"]["condition"]):
                        s = "normal"
                    else:
                        s = "disabled"
                else:
                    s = element["state"]

            button = ctk.CTkButton(surface, text=element["text"], state=s, command=lambda f=f: eval(f), fg_color=theme["fg_color"], hover_color=theme["hover_color"], text_color=theme["text_color"])
            if use_grid:
                button.grid(column=element["grid"]["column"], row=element["grid"]["row"], sticky=element["grid"]["sticky"], padx=element["grid"]["padx"], pady=element["grid"]["pady"])
            else:
                button.pack(pady=element["pad"], padx=element["padx"] if "padx" in element else 0, side=side)
            self.elements["button"][element["id"]] = button

        if etype == "entry":
            theme = self.theme["entry"]

            enable_button = True if "button" in element else False
            if enable_button:
                eframe = ctk.CTkFrame(surface, bg_color="#2b2b2b")
                self.newElement(eframe, element["button"], "button", use_grid)
                self.elements["button"][element["button"]["id"]].pack(side="right")

            width = element["width"] if "width" in element else 200
            height = element["height"] if "height" in element else 30

            parent = eframe if enable_button else surface
            entry = ctk.CTkEntry(parent, placeholder_text=element["text"], width=width, height=height, fg_color=theme["fg_color"])
            if enable_button:
                if self.elements["button"][element["button"]["id"]].cget("state") == "disabled":
                    pass
                else:
                    entry.bind("<Return>", lambda event: eval(element["function"]))
            if not enable_button:
                if use_grid:
                    entry.grid(column=element["grid"]["column"], row=element["grid"]["row"], sticky=element["grid"]["sticky"], padx=element["grid"]["padx"], pady=element["grid"]["pady"])
                else:
                    entry.pack(pady=element["pad"], side=side)
            else:
                entry.pack(pady=5, padx=5, side="left")

            if "default" in element:
                default = element["default"]
                if isinstance(default, dict):
                    default = eval(element["default"]["function"])

                entry.insert(0, default)

            if enable_button:
                eframe.pack(pady=element["pad"], padx=element["padx"] if "padx" in element else 0, side=side)

            self.elements["entry"][element["id"]] = entry

        if etype == "optionmenu":
            theme = self.theme["optionmenu"]
            v = self.data[element["data"]] if not isinstance(element["data"], list) else element["data"]
            optionmenu_frame = ctk.CTkFrame(surface)
            optionmenu_label = ctk.CTkLabel(optionmenu_frame, text=element["text"])
            optionmenu_label.pack(side="left", padx=5)
            optionmenu = ctk.CTkOptionMenu(optionmenu_frame, values=v, fg_color=theme["fg_color"], button_color=theme["button_color"], button_hover_color=theme["button_hover_color"], dropdown_fg_color=theme["dropdown_fg_color"], dropdown_hover_color=theme["dropdown_hover_color"], dropdown_text_color=theme["dropdown_text_color"], text_color=theme["text_color"])
            optionmenu.pack(side="left")
            if use_grid:
                optionmenu_frame.grid(column=element["grid"]["column"], row=element["grid"]["row"], sticky=element["grid"]["sticky"], padx=element["grid"]["padx"], pady=element["grid"]["pady"])
            else:
                optionmenu_frame.pack(pady=element["pad"], padx=element["padx"] if "padx" in element else 0)
            self.elements["optionmenu"][element["id"]] = optionmenu

        if etype == "list":
            list_frame = ctk.CTkFrame(surface)
            list_label = ctk.CTkLabel(list_frame, text=element["text"])
            list_label.pack(padx=5)
            elist = ctk.CTkScrollableFrame(list_frame, width=element["width"], height=element["height"], fg_color="#242424", corner_radius=0)
            elist.pack(side="left")
            if use_grid:
                list_frame.grid(column=element["grid"]["column"], row=element["grid"]["row"], sticky=element["grid"]["sticky"], padx=element["grid"]["padx"], pady=element["grid"]["pady"])
            else:
                list_frame.pack(pady=element["pad"])

            data = element["data"]
            if data["type"] == "appdata":
                data = self.data[data["key"]]
            elif data["type"] == "function":
                data = eval(data["function"])

            for d in data:
                f = element["function"]

                t = eval(element["button_text"])

                theme = self.theme["button"]
                button = ctk.CTkButton(elist, text=t, command=lambda f=f, d=d: eval(f.replace("list-value", f"{d}")), fg_color=theme["fg_color"], hover_color=theme["hover_color"], text_color=theme["text_color"])
                button.pack(pady=5, padx=element["padx"] if "padx" in element else 0)
            self.elements["list"][element["id"]] = elist

        if etype == "switch":
            theme = self.theme["switch"]
            switch = ctk.CTkSwitch(surface, text=element["text"], fg_color=theme["fg_color"], progress_color=theme["progress_color"], button_color=theme["button_color"], button_hover_color=theme["button_hover_color"])
            if use_grid:
                switch.grid(column=element["grid"]["column"], row=element["grid"]["row"], sticky=element["grid"]["sticky"], padx=element["grid"]["padx"], pady=element["grid"]["pady"])
            else:
                switch.pack(pady=element["pad"], padx=element["padx"] if "padx" in element else 0, side=side)

            ef = None if "enable_function" not in element else element["enable_function"]
            df = None if "disable_function" not in element else element["disable_function"]

            enabled = True
            if "enabled" in element:
                if isinstance(element["enabled"], dict):
                    if eval(element["enabled"]["condition"]):
                        enabled = True
                    else:
                        enabled = False
                else:
                    enabled = element["enabled"]

            switch.select() if enabled else switch.deselect()

            self.elements["switch"][element["id"]] = {"obj": switch, "enable_function": ef, "disable_function": df, "state": switch.get()}

        if etype == "textbox":
            font = ("Arial", element["font_size"])
            width = element["width"] if "width" in element else 200
            height = element["height"] if "height" in element else 30
            textbox = ctk.CTkTextbox(surface, width=width, height=height, font=font)
            if use_grid:
                textbox.grid(column=element["grid"]["column"], row=element["grid"]["row"], sticky=element["grid"]["sticky"], padx=element["grid"]["padx"], pady=element["grid"]["pady"])
            else:
                textbox.pack(pady=element["pad"], padx=element["padx"] if "padx" in element else 0, side=side)
            if "default" in element:
                textbox.insert("0.0", element["default"])
            self.elements["textbox"][element["id"]] = {"obj": textbox, "update_with_function": element["update_with_function"]}

        if etype == "progressbar":
            theme = self.theme["progressbar"]
            width = element["width"] if "width" in element else 300
            height = element["height"] if "height" in element else 20

            progressbar = ctk.CTkProgressBar(surface, width=width, height=height, fg_color=theme["fg_color"], progress_color=theme["progress_color"])
            progressbar.set(0)
            if use_grid:
                progressbar.grid(column=element["grid"]["column"], row=element["grid"]["row"], sticky=element["grid"]["sticky"], padx=element["grid"]["padx"], pady=element["grid"]["pady"])
            else:
                progressbar.pack(pady=element["pad"], padx=element["padx"] if "padx" in element else 0, side=side)
            self.elements["progressbar"][element["id"]] = {"obj": progressbar, "value": element["value"]}

        if etype == "segmentedbutton":
            theme = self.theme["segmentedbutton"]
            v = self.data[element["data"]] if not isinstance(element["data"], list) else element["data"]
            segmentedbutton_frame = ctk.CTkFrame(surface)
            segmentedbutton_label = ctk.CTkLabel(segmentedbutton_frame, text=element["text"])
            segmentedbutton_label.pack(side="left", padx=5)

            function = None if "function" not in element else element["function"]

            segmentedbutton = ctk.CTkSegmentedButton(segmentedbutton_frame, values=v, command=lambda v, f=function: eval(f) if f is not None else None, fg_color=theme["fg_color"], selected_color=theme["selected_color"], selected_hover_color=theme["selected_hover_color"], text_color=theme["text_color"])
            segmentedbutton.set(v[0])
            segmentedbutton.pack(side="left")

            if use_grid:
                segmentedbutton_frame.grid(column=element["grid"]["column"], row=element["grid"]["row"], sticky=element["grid"]["sticky"], padx=element["grid"]["padx"], pady=element["grid"]["pady"])
            else:
                segmentedbutton_frame.pack(pady=element["pad"], padx=element["padx"] if "padx" in element else 0)

            self.elements["segmentedbutton"][element["id"]] = segmentedbutton

        if etype == "slider":
            theme = self.theme["slider"]
            slider_frame = ctk.CTkFrame(surface)
            
            width = element["width"] if "width" in element else 300
            height = element["height"] if "height" in element else 20

            minimum = element["min"] if "min" in element else 0
            maximum = element["max"] if "max" in element else 100

            if isinstance(maximum, dict):
                if "variable" in maximum:
                    maximum = eval(maximum["variable"])

            slider = ctk.CTkSlider(slider_frame, width=width, height=height, from_=minimum, to=maximum, number_of_steps=maximum-1, progress_color=theme["progress_color"], button_color=theme["button_color"], button_hover_color=theme["button_hover_color"])
            slider.set(element["default"])
            slider.pack(pady=element["pad"], side=side)

            slider_value_label = ctk.CTkLabel(slider_frame, text=0)
            slider_value_label.pack(padx=5)

            if use_grid:
                slider_frame.grid(column=element["grid"]["column"], row=element["grid"]["row"], sticky=element["grid"]["sticky"], padx=element["grid"]["padx"], pady=element["grid"]["pady"])
            else:
                slider_frame.pack(pady=element["pad"])

            suffix = element["suffix"] if "suffix" in element else ""
            prefix = element["prefix"] if "prefix" in element else ""
            rnd = element["round"] if "round" in element else False
            self.elements["slider"][element["id"]] = {"obj": slider, "value_label": slider_value_label, "prefix": prefix, "suffix": suffix, "rnd": rnd}

        if etype == "image":
            path = element["path"]

            image = Image.open(path).convert("RGBA")
            width = element["width"] if "width" in element else image.width
            height = element["height"] if "height" in element else image.height

            image = image.resize((width, height))
            image = ImageTk.PhotoImage(image)

            image_label = ctk.CTkLabel(surface, image=image, text="", fg_color="transparent")
            image_label.image = image

            if use_grid:
                image_label.grid(column=element["grid"]["column"], row=element["grid"]["row"], sticky=element["grid"]["sticky"], padx=element["grid"]["padx"], pady=element["grid"]["pady"])
            else:
                image_label.pack(pady=element["pad"], padx=element.get("padx", 0), side=side)

            self.elements["image"][element["id"]] = image_label

        if etype == "linegraph":
            theme = self.theme["linegraph"]

            fig = Figure(figsize=(5, 4), dpi=element["size"])
            fig.patch.set_facecolor(element["fg_color"])
            ax = fig.add_subplot(111)
            ax.set_facecolor(element["fg_color"])
            ax.tick_params(axis="both", colors=element["text_color"])

            ax.spines["top"].set_color(theme["spine_color"])
            ax.spines["bottom"].set_color(theme["spine_color"])
            ax.spines["left"].set_color(theme["spine_color"])
            ax.spines["right"].set_color(theme["spine_color"])

            line, = ax.plot([], [], marker="o", linestyle="-")

            ax.set_title(element["title"], color=element["text_color"])
            ax.set_xlabel(element["x_label"], color=element["text_color"])
            ax.set_ylabel(element["y_label"], color=element["text_color"])

            canvas = FigureCanvasTkAgg(fig, master=surface)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(expand=True, fill="both", padx=element["padx"] if "padx" in element else 0, pady=element["pad"] if "pad" in element else 0, side=side)

            x_function = element["x_function"]
            y_function = element["y_function"]

            self.elements["linegraph"][element["id"]] = {"fig": fig, "ax": ax, "line": line, "canvas": canvas, "x": [], "y": [], "x_function": x_function, "y_function": y_function}

    def loadPage(self, page):
        self.data["servers"] = ServerManager.retriveServers()
        self.elements = self.resetElements()
        ServerManager.servers = ServerManager.retriveServers()
        page_path = f"data/pages/{page}.json"
        with open(page_path, "r") as f:
            data = json.load(f)
        
        self.entries = {}
        
        for widget in self.surface.winfo_children():
            widget.destroy()

        self.surface.pack_forget()
        self.surface.pack(fill="both", expand=True)

        if "on_load_function" in data:
            exec(data["on_load_function"])

        use_grid = data["use_grid"] if "use_grid" in data else False
        if use_grid:
            self.surface.grid_columnconfigure(0, weight=1)
            self.surface.grid_rowconfigure(0, weight=1)

        if "background_image" in data:
            page_dir = os.path.dirname(page_path)
            image = Image.open(f'{page_dir}/{data["background_image"]}')
            image = image.resize((862, 519))
            bg_image = ImageTk.PhotoImage(image)

            bg_label = ctk.CTkLabel(self.surface, image=bg_image, text="")
            bg_label.place(relwidth=1, relheight=1)

        for element in data["elements"]:
            self.newElement(self.surface, element, use_grid=use_grid)

    def getFrameCount(self):
        return self.frame_count

    def checks(self):
        for label in self.elements["label"]:
            label_data = self.elements["label"][label]

            if isinstance(label_data["rawtext"], dict):
                if label_data["rawtext"]["type"] == "function" and not label_data["rawtext"]["run_once"]:
                    text = f'{label_data["rawtext"]["prefix"] if "prefix" in label_data["rawtext"] else ""}{eval(label_data["rawtext"]["function"])}{label_data["rawtext"]["suffix"] if "suffix" in label_data["rawtext"] else ""}'

                    label_data["obj"].configure(text=text)

        for switch in self.elements["switch"]:
            switch_data = self.elements["switch"][switch]
            switch_obj = switch_data["obj"]
            switch_state = switch_data["state"]

            if switch_obj.get() == 1 and not switch_state:
                if switch_data["enable_function"] is not None:
                    eval(switch_data["enable_function"])
                switch_data["state"] = True

            elif switch_obj.get() == 0 and switch_state:
                if switch_data["disable_function"] is not None:
                    eval(switch_data["disable_function"])
                switch_data["state"] = False

        for textbox in self.elements["textbox"]:
            textbox_data = self.elements["textbox"][textbox]
            if textbox_data["update_with_function"] is not None:
                text = eval(textbox_data["update_with_function"])
                current_scroll = textbox_data["obj"].yview() 
                
                current_text = textbox_data["obj"].get("0.0", "end").strip()
                if current_text != text.strip():
                    textbox_data["obj"].delete("0.0", "end")
                    textbox_data["obj"].insert("0.0", text)
                
                    textbox_data["obj"].yview_moveto(current_scroll[0])

        for progressbar in self.elements["progressbar"]:
            progressbar_data = self.elements["progressbar"][progressbar]
            progressbar_obj = progressbar_data["obj"]
            progressbar_value = eval(progressbar_data["value"])
            progressbar_obj.set(progressbar_value)

        for slider in self.elements["slider"]:
            slider_data = self.elements["slider"][slider]
            slider_value = slider_data["obj"].get()

            if slider_data["rnd"]:
                slider_value = round(slider_value)

            slider_value_label = slider_data["value_label"]
            text = f'{slider_data["prefix"]}{slider_value}{slider_data["suffix"]}'
            slider_value_label.configure(text=text)

        for linegraph in self.elements["linegraph"]:
            linegraph_data = self.elements["linegraph"][linegraph]
            x_function = linegraph_data["x_function"]
            y_function = linegraph_data["y_function"]

            x = eval(x_function)
            y = eval(y_function)

            linegraph_data["x"].append(x)
            linegraph_data["y"].append(y)

            linegraph_data["line"].set_data(linegraph_data["x"], linegraph_data["y"])

            linegraph_data["fig"].canvas.draw_idle()
            
            linegraph_data["ax"].set_xlim(min(linegraph_data["x"]), max(linegraph_data["x"]) + 1)
            linegraph_data["ax"].set_ylim(min(linegraph_data["y"]) - 1, max(linegraph_data["y"]) + 1)

        self.frame_count += 1
        self.root.after(16, self.checks)
ElementManager = ELEMENTMANAGER()