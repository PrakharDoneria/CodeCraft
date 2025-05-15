"""
Main application class for ChiX Editor
"""

import customtkinter as ctk
import tkinter as tk
import os
import sys
from chix.ui.theme import setup_theme
from chix.ui.panels import MainPanelView
from chix.ui.statusbar import StatusBar
from chix.ui.explorer import FileExplorer
from chix.ui.command_palette import CommandPalette
from chix.core.project import ProjectManager

class ChiXApp:
    """Main application class for ChiX Editor"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.geometry("1400x900")
        self.root.title("ChiX - Professional C Code Editor")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Set up the theme
        setup_theme()
        
        # Shared application state
        self.state = {
            "app": self.root,
            "current_file": None,
            "current_project": None,
            "active_editor": None,
            "editors": {},
            "mode": "compiler",
            "theme_mode": "dark",
            "show_minimap": True,
            "tab_size": 4,
            "word_wrap": False,
            "current_directory": os.getcwd(),
        }
        
        # Project management
        self.project_manager = ProjectManager(self.state)
        self.state["project_manager"] = self.project_manager
        
        # Set up the UI components
        self._setup_ui()
        
        # Set up keyboard shortcuts
        self._setup_keybindings()
    
    def _setup_ui(self):
        """Set up the UI components"""
        # Main layout using PanedWindow for resizable panels
        self.main_paned = tk.PanedWindow(self.root, orient="horizontal", bg="#2b2b2b", sashwidth=4)
        self.main_paned.pack(fill="both", expand=True)
        
        # Left panel (Explorer)
        self.left_frame = ctk.CTkFrame(self.main_paned, width=200)
        self.file_explorer = FileExplorer(self.left_frame, self.state)
        self.file_explorer.pack(fill="both", expand=True)
        
        # Right main content area
        self.right_frame = ctk.CTkFrame(self.main_paned)
        
        # Add panels to PanedWindow
        self.main_paned.add(self.left_frame, width=200)
        self.main_paned.add(self.right_frame, width=1200)
        
        # Create the main panel view in the right frame
        self.main_panel = MainPanelView(self.right_frame, self.state)
        self.main_panel.pack(fill="both", expand=True)
        
        # Create status bar at the bottom
        self.status_bar = StatusBar(self.root, self.state)
        self.status_bar.pack(fill="x", side="bottom")
        self.state["status_bar"] = self.status_bar
        
        # Command palette (hidden by default)
        self.command_palette = CommandPalette(self.root, self.state)
        self.state["command_palette"] = self.command_palette
        
        # Set application credits
        credits = "ChiX Editor by Prakhar Doneria | Open Source: github.com/PrakharDoneria/ChiX"
        self.status_bar.set_credits(credits)
    
    def _setup_keybindings(self):
        """Set up global keyboard shortcuts"""
        # Command palette (Ctrl+Shift+P)
        self.root.bind("<Control-Shift-P>", lambda e: self.command_palette.show())
        self.root.bind("<Control-Shift-p>", lambda e: self.command_palette.show())
        
        # Ctrl+N for new file
        self.root.bind("<Control-n>", lambda e: self.main_panel.create_new_tab())
        
        # Ctrl+W to close current tab
        self.root.bind("<Control-w>", lambda e: self.main_panel.close_current_tab())
        
        # Ctrl+Tab to switch tabs
        self.root.bind("<Control-Tab>", lambda e: self.main_panel.next_tab())
        self.root.bind("<Control-Shift-Tab>", lambda e: self.main_panel.prev_tab())
        
        # F11 for fullscreen toggle
        self.root.bind("<F11>", self.toggle_fullscreen)
    
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))
    
    def on_close(self):
        """Handle application closing"""
        # Check for unsaved changes
        if self.main_panel.has_unsaved_changes():
            dialog = ctk.CTkInputDialog(
                text="You have unsaved changes. Save before exiting?",
                title="Unsaved Changes"
            )
            response = dialog.get_input()
            if response and response.lower() == "y":
                self.main_panel.save_all_tabs()
        
        # Save editor preferences
        self.project_manager.save_editor_state()
        
        # Close the application
        self.root.destroy()
    
    def start(self):
        """Start the application"""
        # Load default project or file if needed
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            if os.path.isfile(file_path):
                self.main_panel.open_file(file_path)
            elif os.path.isdir(file_path):
                self.project_manager.open_project(file_path)
        else:
            # Create a new tab with starter code
            self.main_panel.create_new_tab()
        
        # Start the main loop
        self.root.mainloop()
