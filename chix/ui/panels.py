"""
Panel management for ChiX Editor
"""

import customtkinter as ctk
import tkinter as tk
from chix.ui.tabs import TabView
from chix.ui.widgets import ToolbarButton, ToolbarSeparator
from chix.ui.theme import get_color
from chix.ui.minimap import Minimap
from chix.core.file_ops import new_file, open_file, save_file, save_file_as
import os

class MainPanelView:
    """Main panel view that contains editor and output"""
    
    def __init__(self, parent, state):
        self.parent = parent
        self.state = state
        
        # Create main frame
        self.frame = ctk.CTkFrame(parent)
        self.frame.pack(fill="both", expand=True)
        
        # Create toolbar
        self.toolbar = self._create_toolbar()
        self.toolbar.pack(fill="x", side="top", padx=2, pady=2)
        
        # Create tab view
        self.tab_view = TabView(self.frame, state)
        self.tab_view.pack(fill="both", expand=True)
        
        # Create output pane
        self._create_output_pane()
        
        # Set up initial state
        state["main_panel"] = self
    
    def _create_toolbar(self):
        """Create the main toolbar"""
        toolbar = ctk.CTkFrame(self.frame, height=40, fg_color=get_color("bg_tertiary"))
        
        # File operations section
        file_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        file_frame.pack(side="left", padx=5, pady=5)
        
        # Icons using Unicode characters
        ICONS = {
            "new_file": "📄",
            "open_file": "📂",
            "save_file": "💾",
            "save_as": "📋",
            "run": "▶️",
            "theme": "🌓",
            "settings": "⚙️",
            "undo": "↩️",
            "redo": "↪️",
            "find": "🔍",
            "format": "🔣",
        }
        
        # New file button
        ToolbarButton(
            file_frame,
            text="New",
            icon_text=ICONS["new_file"],
            command=self.create_new_tab,
            tooltip="Create new file (Ctrl+N)"
        ).pack(side="left", padx=2)
        
        # Open file button
        ToolbarButton(
            file_frame,
            text="Open",
            icon_text=ICONS["open_file"],
            command=self.open_file_dialog,
            tooltip="Open file (Ctrl+O)"
        ).pack(side="left", padx=2)
        
        # Save file button
        ToolbarButton(
            file_frame,
            text="Save",
            icon_text=ICONS["save_file"],
            command=self.save_current_tab,
            tooltip="Save file (Ctrl+S)"
        ).pack(side="left", padx=2)
        
        # Save As button
        ToolbarButton(
            file_frame,
            text="Save As",
            icon_text=ICONS["save_as"],
            command=self.save_as_current_tab,
            tooltip="Save file as... (Ctrl+Shift+S)"
        ).pack(side="left", padx=2)
        
        # Add separator
        ToolbarSeparator(toolbar).pack(side="left", padx=10, pady=8)
        
        # Edit operations
        edit_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        edit_frame.pack(side="left", padx=5, pady=5)
        
        # Undo button
        ToolbarButton(
            edit_frame,
            icon_text=ICONS["undo"],
            text="",
            command=self.undo,
            width=40,
            tooltip="Undo (Ctrl+Z)"
        ).pack(side="left", padx=2)
        
        # Redo button
        ToolbarButton(
            edit_frame,
            icon_text=ICONS["redo"],
            text="",
            command=self.redo,
            width=40,
            tooltip="Redo (Ctrl+Y)"
        ).pack(side="left", padx=2)
        
        # Find button
        ToolbarButton(
            edit_frame,
            icon_text=ICONS["find"],
            text="",
            command=self.show_find_replace,
            width=40,
            tooltip="Find and Replace (Ctrl+F)"
        ).pack(side="left", padx=2)
        
        # Format button
        ToolbarButton(
            edit_frame,
            icon_text=ICONS["format"],
            text="",
            command=self.format_code,
            width=40,
            tooltip="Format Code (Ctrl+Shift+F)"
        ).pack(side="left", padx=2)
        
        # Add separator
        ToolbarSeparator(toolbar).pack(side="left", padx=10, pady=8)
        
        # Run operations
        run_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        run_frame.pack(side="left", padx=5, pady=5)
        
        # Run button
        ToolbarButton(
            run_frame,
            text="Run",
            icon_text=ICONS["run"],
            command=self.run_code,
            fg_color="#1e4620",
            hover_color="#2e6830",
            tooltip="Run Code (F5)"
        ).pack(side="left", padx=2)
        
        # Mode selection
        ctk.CTkLabel(
            run_frame,
            text="Mode:"
        ).pack(side="left", padx=(10, 5))
        
        # Mode dropdown
        mode_values = ["compiler", "interpreter"]
        mode_var = tk.StringVar(value=self.state.get("mode", "compiler"))
        
        def on_mode_change(choice):
            self.state["mode"] = choice
        
        mode_dropdown = ctk.CTkOptionMenu(
            run_frame,
            values=mode_values,
            command=on_mode_change,
            variable=mode_var,
            width=120
        )
        mode_dropdown.pack(side="left", padx=5)
        
        # Settings on the right
        settings_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        settings_frame.pack(side="right", padx=5, pady=5)
        
        # Theme toggle
        ToolbarButton(
            settings_frame,
            icon_text=ICONS["theme"],
            text="",
            command=self.toggle_theme,
            width=40,
            tooltip="Toggle Theme"
        ).pack(side="right", padx=2)
        
        # Minimap toggle
        self.minimap_var = tk.BooleanVar(value=self.state.get("show_minimap", True))
        minimap_check = ctk.CTkCheckBox(
            settings_frame,
            text="Minimap",
            variable=self.minimap_var,
            command=self.toggle_minimap,
            width=30
        )
        minimap_check.pack(side="right", padx=10)
        
        return toolbar
    
    def _create_output_pane(self):
        """Create the output pane"""
        # Main container with frame
        self.output_frame = ctk.CTkFrame(self.frame)
        self.output_frame.pack(fill="x", side="bottom", padx=5, pady=(0, 5))
        
        # Output header with title and controls
        header_frame = ctk.CTkFrame(self.output_frame, fg_color=get_color("bg_tertiary"), height=30)
        header_frame.pack(fill="x", side="top")
        
        # Title
        ctk.CTkLabel(
            header_frame,
            text="Console Output",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=10, pady=5)
        
        # Clear button
        ctk.CTkButton(
            header_frame,
            text="Clear",
            width=60,
            height=20,
            command=self.clear_output
        ).pack(side="right", padx=5, pady=5)
        
        # Toggle button 
        self.toggle_btn = ctk.CTkButton(
            header_frame,
            text="▲",
            width=30,
            height=20,
            command=self.toggle_output
        )
        self.toggle_btn.pack(side="right", padx=5, pady=5)
        
        # Output text area
        self.output = ctk.CTkTextbox(
            self.output_frame,
            height=150,
            font=("Cascadia Code", 12),
            fg_color=get_color("bg_primary"),
            text_color="#00ff00",  # Lime green for contrast
            border_width=0,
            corner_radius=0
        )
        self.output.pack(fill="x", expand=True, padx=0, pady=(0, 0))
        
        # Store in state
        self.state["output"] = self.output
    
    def toggle_output(self):
        """Toggle the visibility of the output pane"""
        if self.output.winfo_ismapped():
            self.output.pack_forget()
            self.toggle_btn.configure(text="▼")
        else:
            self.output.pack(fill="x", expand=True, padx=0, pady=(0, 0))
            self.toggle_btn.configure(text="▲")
    
    def clear_output(self):
        """Clear the output console"""
        self.output.delete("1.0", "end")
    
    def create_new_tab(self):
        """Create a new editor tab"""
        starter_code = """#include <stdio.h>

int main() {
    // Your code here
    printf("Hello, World!\\n");
    return 0;
}
"""
        # Create a new tab with starter code
        self.tab_view.create_tab(content=starter_code)
    
    def open_file_dialog(self):
        """Open a file dialog and load selected file"""
        open_file(self.state, on_file_selected=self.tab_view.open_file)
    
    def save_current_tab(self):
        """Save the current tab's content"""
        self.tab_view.save_current_tab()
    
    def save_as_current_tab(self):
        """Save the current tab with a new name"""
        self.tab_view.save_current_tab_as()
    
    def save_all_tabs(self):
        """Save all open tabs"""
        self.tab_view.save_all_tabs()
    
    def has_unsaved_changes(self):
        """Check if any tabs have unsaved changes"""
        return self.tab_view.has_unsaved_changes()
    
    def run_code(self):
        """Run the current file's code"""
        # Get the current editor
        editor = self.tab_view.get_current_editor()
        if not editor:
            return
        
        # Clear the output
        self.clear_output()
        
        # Save first if needed
        if not self.tab_view.get_current_file_path():
            self.save_as_current_tab()
            if not self.tab_view.get_current_file_path():
                self.output.insert("1.0", "[Error] Please save the file before running.\n")
                return
        else:
            self.save_current_tab()
        
        # Make sure output is visible
        if not self.output.winfo_ismapped():
            self.toggle_output()
        
        # Update state with current editor
        self.state["active_editor"] = editor
        
        # Run the code using the current mode
        from chix.core.runner import run_code
        run_code(self.state, mode=self.state.get("mode", "compiler"))
    
    def undo(self):
        """Undo the last change in the current editor"""
        editor = self.tab_view.get_current_editor()
        if editor:
            editor._undo()
    
    def redo(self):
        """Redo the last undone change in the current editor"""
        editor = self.tab_view.get_current_editor()
        if editor:
            editor._redo()
    
    def show_find_replace(self):
        """Show the find and replace dialog"""
        self.tab_view.show_find_replace()
    
    def format_code(self):
        """Format the current code"""
        editor = self.tab_view.get_current_editor()
        if editor:
            from chix.utils.formatter import format_c_code
            code = editor.get("1.0", "end-1c")
            formatted_code = format_c_code(code)
            if formatted_code:
                editor.delete("1.0", "end")
                editor.insert("1.0", formatted_code)
                editor._on_text_changed()
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        from chix.ui.theme import cycle_theme, setup_theme
        new_theme = cycle_theme()
        setup_theme()
        
        # Update all UI elements
        self.state["status_bar"].update_theme()
        self.tab_view.update_theme()
    
    def toggle_minimap(self):
        """Toggle the minimap visibility"""
        show_minimap = self.minimap_var.get()
        self.state["show_minimap"] = show_minimap
        self.tab_view.set_minimap_visibility(show_minimap)
    
    def pack(self, **kwargs):
        """Pack the main panel"""
        self.frame.pack(**kwargs)
