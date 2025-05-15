"""
Status bar for ChiX Editor
"""

import customtkinter as ctk
import tkinter as tk
import os
from chix.ui.theme import get_color
import webbrowser
import time

class StatusBar:
    """Status bar shown at the bottom of the editor"""
    
    def __init__(self, parent, state):
        self.parent = parent
        self.state = state
        
        # Create main container
        self.frame = ctk.CTkFrame(parent, height=25, fg_color=get_color("accent_primary"))
        
        # Left side status elements
        self.left_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.left_frame.pack(side="left", fill="y")
        
        # File info
        self.file_info = ctk.CTkLabel(
            self.left_frame, 
            text="No file opened", 
            text_color="#ffffff", 
            font=("Arial", 11)
        )
        self.file_info.pack(side="left", padx=10)
        
        # Status message (middle)
        self.status_message = ctk.CTkLabel(
            self.frame, 
            text="", 
            text_color="#ffffff", 
            font=("Arial", 11)
        )
        self.status_message.pack(side="left", padx=10, expand=True)
        
        # Right side status elements
        self.right_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.right_frame.pack(side="right", fill="y")
        
        # Mode indicator (compiler/interpreter)
        self.mode_indicator = ctk.CTkLabel(
            self.right_frame,
            text="Compiler Mode",
            font=("Arial", 11),
            text_color="#ffffff",
            fg_color=get_color("bg_tertiary"),
            corner_radius=3,
            padx=5,
            pady=2
        )
        self.mode_indicator.pack(side="right", padx=10)
        
        # Position indicator (line, column)
        self.position_indicator = ctk.CTkLabel(
            self.right_frame, 
            text="Ln 1, Col 1", 
            text_color="#ffffff", 
            font=("Arial", 11)
        )
        self.position_indicator.pack(side="right", padx=10)
        
        # Credits (clickable GitHub link)
        self.credits_frame = ctk.CTkFrame(self.right_frame, fg_color=get_color("bg_tertiary"), corner_radius=3)
        self.credits_frame.pack(side="right", padx=10, pady=2)
        
        self.credits = ctk.CTkLabel(
            self.credits_frame, 
            text="", 
            text_color="#00FFFF", 
            font=("Arial", 11, "bold"),
            cursor="hand2",
            padx=5,
            pady=2
        )
        self.credits.pack()
        
        # Make credits clickable
        self.credits.bind("<Button-1>", self._open_github)
        
        # Update mode indicator based on state
        self._update_mode_indicator()
        
        # Start cursor position tracking if editor exists
        if "active_editor" in state and state["active_editor"]:
            self._start_position_tracking(state["active_editor"])
        
        # Temporary message timer
        self.message_timer = None
    
    def _open_github(self, event):
        """Open GitHub repository"""
        webbrowser.open("https://github.com/PrakharDoneria/ChiX")
    
    def _update_mode_indicator(self):
        """Update the mode indicator based on current state"""
        mode = self.state.get("mode", "compiler")
        if mode == "compiler":
            self.mode_indicator.configure(text="Compiler Mode")
        else:
            self.mode_indicator.configure(text="Interpreter Mode")
    
    def _start_position_tracking(self, editor):
        """Start tracking cursor position in the editor"""
        editor.bind("<ButtonRelease-1>", self._update_position)
        editor.bind("<KeyRelease>", self._update_position)
    
    def _update_position(self, event=None):
        """Update cursor position display"""
        if event and hasattr(event, "widget"):
            try:
                widget = event.widget
                position = widget.index(tk.INSERT)
                line, col = position.split(".")
                self.position_indicator.configure(text=f"Ln {line}, Col {int(col)+1}")
            except Exception:
                pass
    
    def update_file_info(self, file_path=None):
        """Update the file information display"""
        if file_path:
            if file_path == "Untitled":
                self.file_info.configure(text="Untitled")
            else:
                filename = os.path.basename(file_path)
                self.file_info.configure(text=f"{filename}")
        else:
            self.file_info.configure(text="No file opened")
    
    def set_message(self, message, timeout_ms=5000):
        """Set a temporary status message with timeout"""
        self.status_message.configure(text=message)
        
        # Clear previous timer if exists
        if self.message_timer:
            self.parent.after_cancel(self.message_timer)
        
        # Set new timer to clear message
        if timeout_ms > 0:
            self.message_timer = self.parent.after(timeout_ms, self.clear_message)
    
    def clear_message(self):
        """Clear the status message"""
        self.status_message.configure(text="")
        self.message_timer = None
    
    def set_credits(self, text):
        """Set the credits text"""
        self.credits.configure(text=text)
    
    def update_theme(self):
        """Update colors when theme changes"""
        self.frame.configure(fg_color=get_color("accent_primary"))
        self.credits_frame.configure(fg_color=get_color("bg_tertiary"))
        self.mode_indicator.configure(fg_color=get_color("bg_tertiary"))
    
    def pack(self, **kwargs):
        """Pack the status bar"""
        self.frame.pack(**kwargs)
