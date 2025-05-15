import customtkinter as ctk
from core.file_ops import new_file, open_file, save_file, save_file_as
from core.runner import run_code
from utils.highlighter import highlight
import os
import tkinter as tk
import webbrowser  # Added for making the credits clickable

# Unicode icons (no external files needed)
ICONS = {
    "new_file": "📄",       # Document
    "open_file": "📂",      # Folder
    "save_file": "💾",      # Floppy disk
    "save_as": "📋",        # Clipboard
    "run": "▶️",            # Play button
    "theme": "🌓",          # Half moon
    "settings": "⚙️",       # Gear
    "undo": "↩️",           # Return arrow
    "redo": "↪️",           # Forward arrow
    "cut": "✂️",            # Scissors
    "copy": "📑",           # Copy
    "paste": "📌",          # Pin
}

class LineNumbers(ctk.CTkCanvas):
    def __init__(self, parent, text_widget, **kwargs):
        # Remove invalid parameters for tkinter Canvas
        if "bg_color" in kwargs:
            bg_color = kwargs.pop("bg_color")
            kwargs["bg"] = bg_color  # Use proper bg parameter
        
        super().__init__(parent, width=30, **kwargs)
        self.text_widget = text_widget
        self.text_widget.bind('<KeyRelease>', self.on_key_release)
        self.text_widget.bind('<MouseWheel>', self.on_key_release)
        self.text_widget.bind('<Configure>', self.on_key_release)
        self.font = ("Consolas", 12)
        self.update_line_numbers()
        
    def on_key_release(self, event=None):
        self.update_line_numbers()
        
    def update_line_numbers(self):
        self.delete("all")
        line_count = int(self.text_widget.index('end-1c').split('.')[0])
        
        for i in range(1, line_count + 1):
            y_coord = self.text_widget.dlineinfo(f"{i}.0")
            if y_coord:
                self.create_text(15, y_coord[1]+2, text=str(i), fill="#606366", font=self.font)

class EnhancedTextbox(ctk.CTkTextbox):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Add key bindings for common IDE shortcuts
        self.bind('<Tab>', self._handle_tab)
        self.bind('<Control-s>', self._handle_save)
        self.bind('<Control-a>', self._handle_select_all)
        self.bind('<Control-z>', self._handle_undo)
        self.bind('<Control-y>', self._handle_redo)
        
    def _handle_tab(self, event):
        self.insert(ctk.INSERT, "    ")  # 4 spaces
        return "break"
        
    def _handle_save(self, event):
        if hasattr(self, "state") and self.state:
            save_file(self.state)
        return "break"
        
    def _handle_select_all(self, event):
        self.tag_add(ctk.SEL, "1.0", ctk.END)
        self.mark_set(ctk.INSERT, "1.0")
        self.see(ctk.INSERT)
        return "break"
        
    def _handle_undo(self, event):
        try:
            self.edit_undo()
        except:
            pass
        return "break"
        
    def _handle_redo(self, event):
        try:
            self.edit_redo()
        except:
            pass
        return "break"

def create_editor(parent, state):
    editor_frame = ctk.CTkFrame(parent)
    editor_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))
    
    # Create Text widget with enhanced functionality
    editor = EnhancedTextbox(
        editor_frame, 
        font=("Consolas", 14), 
        wrap="none", 
        activate_scrollbars=True,
        fg_color="#1e1e1e",
        border_width=0,
        corner_radius=0
    )
    
    # Add line numbers
    line_numbers = LineNumbers(
        editor_frame, 
        editor, 
        bg="#262626",  # Using standard bg parameter
        highlightthickness=0
    )
    
    # Pack widgets
    line_numbers.pack(side="left", fill="y", padx=(0, 0))
    editor.pack(side="right", fill="both", expand=True)
    
    # Store line numbers in state for updating
    state["line_numbers"] = line_numbers
    
    # Store state reference in editor
    editor.state = state
    
    return editor

def create_output(parent):
    output_frame = ctk.CTkFrame(parent)
    output_frame.pack(fill="x", padx=10, pady=(0, 5))
    
    # Output label
    output_label = ctk.CTkLabel(output_frame, text="Console Output", anchor="w", font=("Arial", 12, "bold"))
    output_label.pack(fill="x", padx=5, pady=(5, 0))
    
    # Actual output area
    output = ctk.CTkTextbox(
        output_frame, 
        height=150, 
        font=("Consolas", 12), 
        text_color="lime",
        fg_color="#262626",
        border_width=0,
        corner_radius=0
    )
    output.pack(fill="x", padx=0, pady=(5, 0))
    
    return output

def create_menu(parent, state):
    # Main toolbar frame
    frame = ctk.CTkFrame(parent, height=40, fg_color="#2d2d30")
    frame.pack(fill="x", padx=0, pady=0)
    
    # Button style
    button_style = {
        "corner_radius": 4,
        "height": 32,
        "width": 80,
        "fg_color": "#3e3e42",
        "hover_color": "#505050",
        "text_color": "white",
        "border_spacing": 10
    }
    
    icon_button_style = {**button_style, "width": 40}
    
    # File operations
    file_frame = ctk.CTkFrame(frame, fg_color="transparent")
    file_frame.pack(side="left", padx=(10, 0), pady=5)
    
    # New button with icon
    new_btn = ctk.CTkButton(
        file_frame, 
        text=f" {ICONS['new_file']} New", 
        command=lambda: new_file(state), 
        **button_style
    )
    new_btn.pack(side="left", padx=2)
    
    # Open button with icon
    open_btn = ctk.CTkButton(
        file_frame, 
        text=f" {ICONS['open_file']} Open", 
        command=lambda: open_file(state, highlight), 
        **button_style
    )
    open_btn.pack(side="left", padx=2)
    
    # Save button with icon
    save_btn = ctk.CTkButton(
        file_frame, 
        text=f" {ICONS['save_file']} Save", 
        command=lambda: save_file(state), 
        **button_style
    )
    save_btn.pack(side="left", padx=2)
    
    # Save As button with icon
    saveas_btn = ctk.CTkButton(
        file_frame, 
        text=f" {ICONS['save_as']} Save As", 
        command=lambda: save_file_as(state), 
        **icon_button_style
    )
    saveas_btn.pack(side="left", padx=2)
    
    # Separator
    separator = ctk.CTkFrame(frame, width=2, height=32, fg_color="#555555")
    separator.pack(side="left", padx=10, pady=5)
    
    # Run operations
    run_frame = ctk.CTkFrame(frame, fg_color="transparent")
    run_frame.pack(side="left", padx=0, pady=5)
    
    # Run button with icon
    run_btn = ctk.CTkButton(
        run_frame, 
        text=f" {ICONS['run']} Run", 
        command=lambda: run_code(state, mode=state.get("mode", "compiler")), 
        **{**button_style, "fg_color": "#1e4620", "hover_color": "#2e6830"}
    )
    run_btn.pack(side="left", padx=2)

    # Add mode selection dropdown
    mode_label = ctk.CTkLabel(frame, text="Mode: ", text_color="white")
    mode_label.pack(side="left", padx=(10, 0))
    mode_selector = ctk.CTkOptionMenu(
        frame,
        values=["compiler", "interpreter"],
        command=lambda selected: state.update({"mode": selected})
    )
    mode_selector.set("compiler")  # Default mode
    mode_selector.pack(side="left", padx=(5, 10))
    
    # Edit operations
    edit_frame = ctk.CTkFrame(frame, fg_color="transparent")
    edit_frame.pack(side="left", padx=10, pady=5)
    
    # Undo button with icon
    undo_btn = ctk.CTkButton(
        edit_frame, 
        text=f" {ICONS['undo']}", 
        command=lambda: state["editor"].edit_undo() if "editor" in state else None, 
        **icon_button_style
    )
    undo_btn.pack(side="left", padx=2)
    
    # Redo button with icon
    redo_btn = ctk.CTkButton(
        edit_frame, 
        text=f" {ICONS['redo']}", 
        command=lambda: state["editor"].edit_redo() if "editor" in state else None, 
        **icon_button_style
    )
    redo_btn.pack(side="left", padx=2)
    
    # Theme switcher on the right
    theme_frame = ctk.CTkFrame(frame, fg_color="transparent")
    theme_frame.pack(side="right", padx=10, pady=5)
    
    # Theme selector
    def toggle_theme():
        current = ctk.get_appearance_mode()
        new_theme = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new_theme)
    
    theme_btn = ctk.CTkButton(
        theme_frame, 
        text=f" {ICONS['theme']} Theme", 
        command=toggle_theme, 
        **icon_button_style
    )
    theme_btn.pack(side="right", padx=2)
    
    # Add About button
    about_btn = ctk.CTkButton(
        theme_frame, 
        text="About", 
        command=lambda: show_about_dialog(parent), 
        **button_style
    )
    about_btn.pack(side="right", padx=5)
    
    return frame

def show_about_dialog(parent):
    about_window = ctk.CTkToplevel(parent)
    about_window.title("About ChiX")
    about_window.geometry("400x200")
    about_window.resizable(False, False)
    
    # Center on screen
    about_window.update_idletasks()
    width = about_window.winfo_width()
    height = about_window.winfo_height()
    x = (about_window.winfo_screenwidth() // 2) - (width // 2)
    y = (about_window.winfo_screenheight() // 2) - (height // 2)
    about_window.geometry(f'{width}x{height}+{x}+{y}')
    
    # Add content
    ctk.CTkLabel(
        about_window,
        text="ChiX - C Code Editor & Runner",
        font=("Arial", 16, "bold")
    ).pack(pady=(20, 5))
    
    ctk.CTkLabel(
        about_window,
        text="Created by Prakhar Doneria",
        font=("Arial", 14)
    ).pack(pady=5)
    
    ctk.CTkLabel(
        about_window,
        text="© 2025 - Open Source Project",
        font=("Arial", 12)
    ).pack(pady=5)
    
    # GitHub link
    def open_github():
        webbrowser.open("https://github.com/PrakharDoneria/ChiX")
    
    ctk.CTkButton(
        about_window,
        text="Visit GitHub Repository",
        command=open_github
    ).pack(pady=15)

class StatusBar(ctk.CTkFrame):
    def __init__(self, parent, state, **kwargs):
        super().__init__(parent, height=25, fg_color="#007acc", **kwargs)
        
        # Current file info (left side)
        self.file_info = ctk.CTkLabel(
            self, 
            text="No file opened", 
            text_color="#ffffff", 
            font=("Arial", 11)
        )
        self.file_info.pack(side="left", padx=10)
        
        # Line/column indicator (right side)
        self.position_indicator = ctk.CTkLabel(
            self, 
            text="Ln 1, Col 1", 
            text_color="#ffffff", 
            font=("Arial", 11)
        )
        self.position_indicator.pack(side="right", padx=10)
        
        # Create a dedicated credits frame with distinct background
        self.credits_frame = ctk.CTkFrame(self, fg_color="#333333", corner_radius=8)
        self.credits_frame.pack(side="right", padx=10, pady=2)
        
        # Credits/GitHub link with enhanced visibility
        self.credits = ctk.CTkLabel(
            self.credits_frame, 
            text="", 
            text_color="#00FFFF",  # Cyan color for high contrast
            font=("Arial", 12, "bold"),
            padx=8,
            pady=2,
            cursor="hand2"  # Hand cursor to indicate clickability
        )
        self.credits.pack()
        
        # Make credits clickable
        self.credits.bind("<Button-1>", self._open_github)
        
        # Setup cursor position tracking
        if state and "editor" in state and state["editor"]:
            state["editor"].bind("<KeyRelease>", self.update_position)
            state["editor"].bind("<Button-1>", self.update_position)
    
    def _open_github(self, event):
        webbrowser.open("https://github.com/PrakharDoneria/ChiX")
            
    def update_file_info(self, filepath=None):
        if filepath:
            filename = os.path.basename(filepath)
            self.file_info.configure(text=f"File: {filename}")
        else:
            self.file_info.configure(text="No file opened")
            
    def update_position(self, event=None):
        if event and hasattr(event, "widget"):
            try:
                position = event.widget.index(ctk.INSERT)
                line, col = position.split(".")
                self.position_indicator.configure(text=f"Ln {line}, Col {int(col)+1}")
            except:
                pass
                
    def set_credits(self, text):
        self.credits.configure(text=text)

def create_status_bar(parent, state):
    status_bar = StatusBar(parent, state)
    status_bar.pack(fill="x", side="bottom")
    
    # Initialize with current file
    if "current_file" in state and state["current_file"]:
        status_bar.update_file_info(state["current_file"])
        
    return status_bar