"""
Command palette for ChiX (VS Code style)
"""

import customtkinter as ctk
import tkinter as tk
from chix.ui.theme import get_color

class CommandPalette:
    """VS Code-style command palette for quick actions"""
    
    def __init__(self, parent, state):
        self.parent = parent
        self.state = state
        self.visible = False
        
        # Create the palette window (initially hidden)
        self.window = ctk.CTkToplevel(parent)
        self.window.withdraw()  # Hide initially
        self.window.overrideredirect(True)  # Remove window decorations
        self.window.attributes("-topmost", True)  # Stay on top
        
        # Set size and position
        self.window.geometry("600x400")
        
        # Create main frame
        self.frame = ctk.CTkFrame(self.window, corner_radius=8)
        self.frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(
            self.frame,
            placeholder_text="Type a command or search...",
            height=40,
            font=("Arial", 14),
            textvariable=self.search_var
        )
        self.search_entry.pack(fill="x", padx=10, pady=10)
        
        # Bind events to search entry
        self.search_entry.bind("<KeyRelease>", self.filter_commands)
        self.search_entry.bind("<Return>", self.execute_selected)
        self.search_entry.bind("<Escape>", self.hide)
        self.search_entry.bind("<Down>", self.select_next)
        self.search_entry.bind("<Up>", self.select_prev)
        
        # Command listbox
        self.command_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.command_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Use Tkinter Listbox for better control
        self.listbox = tk.Listbox(
            self.command_frame,
            bg=get_color("bg_primary"),
            fg=get_color("fg_primary"),
            selectbackground=get_color("selection"),
            selectforeground=get_color("fg_primary"),
            font=("Arial", 12),
            borderwidth=0,
            highlightthickness=0
        )
        self.listbox.pack(fill="both", expand=True)
        
        # Bind listbox events
        self.listbox.bind("<Double-Button-1>", self.execute_selected)
        
        # Scrollbar for listbox
        scrollbar = ctk.CTkScrollbar(self.command_frame, command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        # Register commands
        self.commands = self._register_commands()
        
        # Current filtered commands
        self.filtered_commands = []
    
    def _register_commands(self):
        """Register all available commands"""
        commands = [
            {
                "name": "New File",
                "description": "Create a new file",
                "shortcut": "Ctrl+N",
                "action": lambda: self.state["main_panel"].create_new_tab()
            },
            {
                "name": "Open File",
                "description": "Open a file from disk",
                "shortcut": "Ctrl+O",
                "action": lambda: self.state["main_panel"].open_file_dialog()
            },
            {
                "name": "Save",
                "description": "Save the current file",
                "shortcut": "Ctrl+S",
                "action": lambda: self.state["main_panel"].save_current_tab()
            },
            {
                "name": "Save As",
                "description": "Save the current file with a new name",
                "shortcut": "Ctrl+Shift+S",
                "action": lambda: self.state["main_panel"].save_as_current_tab()
            },
            {
                "name": "Close Tab",
                "description": "Close the current tab",
                "shortcut": "Ctrl+W",
                "action": lambda: self.state["main_panel"].tab_view.close_tab(
                    self.state["main_panel"].tab_view.current_tab_id
                )
            },
            {
                "name": "Save All",
                "description": "Save all open files",
                "shortcut": "Ctrl+Alt+S",
                "action": lambda: self.state["main_panel"].save_all_tabs()
            },
            {
                "name": "Find and Replace",
                "description": "Open find and replace dialog",
                "shortcut": "Ctrl+F",
                "action": lambda: self.state["main_panel"].show_find_replace()
            },
            {
                "name": "Run Program",
                "description": "Run the current program",
                "shortcut": "F5",
                "action": lambda: self.state["main_panel"].run_code()
            },
            {
                "name": "Toggle Theme",
                "description": "Switch between light and dark themes",
                "shortcut": "Alt+T",
                "action": lambda: self.state["main_panel"].toggle_theme()
            },
            {
                "name": "Format Code",
                "description": "Format the current code",
                "shortcut": "Ctrl+Shift+F",
                "action": lambda: self.state["main_panel"].format_code()
            },
            {
                "name": "Toggle Minimap",
                "description": "Show or hide the code minimap",
                "shortcut": "Alt+M",
                "action": lambda: self.state["main_panel"].toggle_minimap()
            },
            {
                "name": "Toggle Output Panel",
                "description": "Show or hide the output panel",
                "shortcut": "Ctrl+`",
                "action": lambda: self.state["main_panel"].toggle_output()
            },
            {
                "name": "Clear Output",
                "description": "Clear the output console",
                "shortcut": "Alt+C",
                "action": lambda: self.state["main_panel"].clear_output()
            },
            {
                "name": "About ChiX",
                "description": "Show about dialog",
                "shortcut": "F1",
                "action": lambda: self._show_about()
            },
            {
                "name": "Exit",
                "description": "Exit the application",
                "shortcut": "Alt+F4",
                "action": lambda: self.state["app"].destroy()
            }
        ]
        
        return commands
    
    def _show_about(self):
        """Show the about dialog"""
        # Import here to avoid circular imports
        from chix.ui.widgets import show_about_dialog
        show_about_dialog(self.parent)
    
    def filter_commands(self, event=None):
        """Filter commands based on search text"""
        search_text = self.search_var.get().lower()
        
        # Clear listbox
        self.listbox.delete(0, tk.END)
        
        # Filter commands
        self.filtered_commands = []
        for cmd in self.commands:
            if (search_text in cmd["name"].lower() or 
                search_text in cmd["description"].lower()):
                self.filtered_commands.append(cmd)
                
                # Format display string
                display = f"{cmd['name']} - {cmd['description']} ({cmd['shortcut']})"
                self.listbox.insert(tk.END, display)
        
        # Select first item if available
        if self.listbox.size() > 0:
            self.listbox.selection_set(0)
    
    def execute_selected(self, event=None):
        """Execute the selected command"""
        selection = self.listbox.curselection()
        if selection and self.filtered_commands:
            index = selection[0]
            if 0 <= index < len(self.filtered_commands):
                command = self.filtered_commands[index]
                self.hide()
                if command["action"]:
                    command["action"]()
    
    def select_next(self, event=None):
        """Select the next command in the listbox"""
        if self.listbox.size() == 0:
            return "break"
            
        try:
            current = self.listbox.curselection()[0]
            self.listbox.selection_clear(current)
            
            # Select next, wrapping around
            next_index = (current + 1) % self.listbox.size()
            self.listbox.selection_set(next_index)
            self.listbox.see(next_index)
        except (IndexError, tk.TclError):
            # No current selection, select first item
            if self.listbox.size() > 0:
                self.listbox.selection_set(0)
                self.listbox.see(0)
        
        return "break"  # Prevent default behavior
    
    def select_prev(self, event=None):
        """Select the previous command in the listbox"""
        if self.listbox.size() == 0:
            return "break"
            
        try:
            current = self.listbox.curselection()[0]
            self.listbox.selection_clear(current)
            
            # Select previous, wrapping around
            prev_index = (current - 1) % self.listbox.size()
            self.listbox.selection_set(prev_index)
            self.listbox.see(prev_index)
        except (IndexError, tk.TclError):
            # No current selection, select last item
            last = self.listbox.size() - 1
            if last >= 0:
                self.listbox.selection_set(last)
                self.listbox.see(last)
        
        return "break"  # Prevent default behavior
    
    def show(self):
        """Show the command palette"""
        if self.visible:
            return
            
        # Center in parent window
        parent_x = self.parent.winfo_rootx() + (self.parent.winfo_width() // 2)
        parent_y = self.parent.winfo_rooty() + (self.parent.winfo_height() // 3)
        
        width = 600
        height = 400
        x = parent_x - (width // 2)
        y = parent_y - (height // 2)
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Show window
        self.window.deiconify()
        self.visible = True
        
        # Reset search
        self.search_var.set("")
        self.search_entry.focus_set()
        
        # Load all commands
        self.filter_commands()
    
    def hide(self, event=None):
        """Hide the command palette"""
        if not self.visible:
            return
            
        self.window.withdraw()
        self.visible = False
        
        # Return focus to editor if available
        if self.state["active_editor"]:
            self.state["active_editor"].focus_set()
