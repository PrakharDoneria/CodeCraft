"""
Keyboard shortcut management for ChiX Editor
Allows defining and customizing keyboard shortcuts
"""

import json
import os
import tkinter as tk

class KeyBindings:
    """Manages keyboard shortcuts for the editor"""
    
    # Default keybindings configuration
    DEFAULT_BINDINGS = {
        # File operations
        "new_file": "<Control-n>",
        "open_file": "<Control-o>",
        "save_file": "<Control-s>",
        "save_file_as": "<Control-Shift-s>",
        "close_file": "<Control-w>",
        "exit": "<Control-q>",
        
        # Editing operations
        "undo": "<Control-z>",
        "redo": "<Control-y>",
        "cut": "<Control-x>",
        "copy": "<Control-c>",
        "paste": "<Control-v>",
        "select_all": "<Control-a>",
        "find": "<Control-f>",
        "replace": "<Control-h>",
        "goto_line": "<Control-g>",
        "indent": "<Tab>",
        "dedent": "<Shift-Tab>",
        "comment": "<Control-slash>",
        "format_code": "<Control-Shift-f>",
        
        # Navigation
        "next_tab": "<Control-Tab>",
        "prev_tab": "<Control-Shift-Tab>",
        "switch_to_tab_1": "<Alt-1>",
        "switch_to_tab_2": "<Alt-2>",
        "switch_to_tab_3": "<Alt-3>",
        "switch_to_tab_4": "<Alt-4>",
        "switch_to_tab_5": "<Alt-5>",
        "switch_to_tab_6": "<Alt-6>",
        "switch_to_tab_7": "<Alt-7>",
        "switch_to_tab_8": "<Alt-8>",
        "switch_to_tab_9": "<Alt-9>",
        
        # View operations
        "zoom_in": "<Control-plus>",
        "zoom_out": "<Control-minus>",
        "toggle_fullscreen": "<F11>",
        "toggle_sidebar": "<Control-b>",
        "toggle_output": "<Control-j>",
        "toggle_minimap": "<Alt-m>",
        
        # Run operations
        "run_code": "<F5>",
        "compile_only": "<Shift-F5>",
        "stop_execution": "<Shift-F5>",
        
        # UI operations
        "command_palette": "<Control-Shift-p>",
        "toggle_theme": "<Alt-t>",
    }
    
    def __init__(self, app, state):
        """
        Initialize the keybindings manager
        
        Args:
            app: The root application widget
            state: The application state
        """
        self.app = app
        self.state = state
        self.bindings = self.DEFAULT_BINDINGS.copy()
        
        # Command handlers dictionary
        self.handlers = {}
        
        # Keybinding status
        self.enabled = True
    
    def load_from_file(self, file_path):
        """
        Load keybindings from a JSON file
        
        Args:
            file_path: Path to the keybindings JSON file
        
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    user_bindings = json.load(f)
                    
                    # Validate and merge bindings
                    for command, key in user_bindings.items():
                        if command in self.bindings:
                            self.bindings[command] = key
                
                return True
        except Exception as e:
            print(f"Error loading keybindings: {e}")
        
        return False
    
    def save_to_file(self, file_path):
        """
        Save current keybindings to a JSON file
        
        Args:
            file_path: Path where to save the keybindings
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(self.bindings, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving keybindings: {e}")
            return False
    
    def register_handler(self, command, handler):
        """
        Register a handler function for a command
        
        Args:
            command: The command identifier
            handler: The function to call when the command is triggered
        """
        self.handlers[command] = handler
    
    def apply_bindings(self):
        """Apply all registered keybindings to the application"""
        if not self.app:
            return
        
        # Clear existing bindings first
        for command in self.bindings:
            key = self.bindings[command]
            try:
                self.app.unbind(key)
            except:
                pass
        
        # Apply new bindings
        for command, key in self.bindings.items():
            if command in self.handlers:
                handler = self.handlers[command]
                self.app.bind(key, lambda event, h=handler: self._handle_command(h, event))
    
    def _handle_command(self, handler, event):
        """Handle a keybinding command"""
        if self.enabled:
            return handler(event)
        return None
    
    def get_binding(self, command):
        """Get the current keybinding for a command"""
        return self.bindings.get(command, "")
    
    def set_binding(self, command, key):
        """
        Set a new keybinding for a command
        
        Args:
            command: The command identifier
            key: The new keybinding (e.g., "<Control-s>")
        
        Returns:
            bool: True if binding was set successfully
        """
        if command in self.bindings:
            # Remove existing binding if another command uses this key
            for cmd, binding in self.bindings.items():
                if binding == key and cmd != command:
                    self.bindings[cmd] = ""
            
            # Set the new binding
            self.bindings[command] = key
            
            # Re-apply bindings
            self.apply_bindings()
            return True
        
        return False
    
    def reset_to_defaults(self):
        """Reset all keybindings to their default values"""
        self.bindings = self.DEFAULT_BINDINGS.copy()
        self.apply_bindings()
    
    def enable(self):
        """Enable keybindings"""
        self.enabled = True
    
    def disable(self):
        """Disable keybindings temporarily"""
        self.enabled = False
    
    def get_key_display_text(self, binding):
        """
        Convert a keybinding to a readable display text
        
        Args:
            binding: Keybinding string (e.g., "<Control-s>")
            
        Returns:
            str: Human-readable text (e.g., "Ctrl+S")
        """
        if not binding:
            return ""
        
        # Remove angle brackets
        text = binding.replace("<", "").replace(">", "")
        
        # Replace modifier keys with readable versions
        text = text.replace("Control", "Ctrl")
        text = text.replace("Alt", "Alt")
        text = text.replace("Shift", "Shift")
        
        # Replace special keys
        text = text.replace("plus", "+")
        text = text.replace("minus", "-")
        text = text.replace("slash", "/")
        text = text.replace("backslash", "\\")
        text = text.replace("period", ".")
        text = text.replace("comma", ",")
        text = text.replace("space", "Space")
        text = text.replace("Tab", "Tab")
        text = text.replace("Return", "Enter")
        text = text.replace("Escape", "Esc")
        
        # Add plus signs between parts
        parts = text.split("-")
        return "+".join(parts)
    
    def get_all_commands(self):
        """
        Get a list of all available commands with their keybindings
        
        Returns:
            list: List of dictionaries with command info
        """
        commands = []
        for command, binding in self.bindings.items():
            # Convert command_name to display name
            display_name = " ".join(word.capitalize() for word in command.split("_"))
            display_key = self.get_key_display_text(binding)
            
            commands.append({
                "id": command,
                "name": display_name,
                "binding": binding,
                "display_key": display_key
            })
        
        return commands

class ShortcutDialog:
    """Dialog for viewing and customizing keyboard shortcuts"""
    
    def __init__(self, parent, keybindings):
        """
        Initialize the keyboard shortcut dialog
        
        Args:
            parent: Parent widget
            keybindings: KeyBindings instance
        """
        self.parent = parent
        self.keybindings = keybindings
        self.dialog = None
    
    def show(self):
        """Show the keyboard shortcut dialog"""
        if self.dialog:
            self.dialog.deiconify()
            self.dialog.lift()
            return
        
        # Create dialog window
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Keyboard Shortcuts")
        self.dialog.geometry("550x400")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog on parent
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() // 2) - 275
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() // 2) - 200
        self.dialog.geometry(f"+{x}+{y}")
        
        # Create main frame
        main_frame = tk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create category labels and listbox headers
        header_frame = tk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 5))
        
        tk.Label(header_frame, text="Command", width=30, anchor="w", font=("Arial", 10, "bold")).pack(side="left")
        tk.Label(header_frame, text="Shortcut", width=20, anchor="w", font=("Arial", 10, "bold")).pack(side="left")
        
        # Create scrollable frame for shortcuts
        scrollframe = tk.Frame(main_frame)
        scrollframe.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(scrollframe, borderwidth=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(scrollframe, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        shortcuts_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=shortcuts_frame, anchor="nw")
        
        # Populate with commands
        commands = self.keybindings.get_all_commands()
        
        # Group commands by category
        categories = {
            "File": ["new_file", "open_file", "save_file", "save_file_as", "close_file", "exit"],
            "Edit": ["undo", "redo", "cut", "copy", "paste", "select_all", "find", "replace", 
                     "goto_line", "indent", "dedent", "comment", "format_code"],
            "View": ["zoom_in", "zoom_out", "toggle_fullscreen", "toggle_sidebar", 
                     "toggle_output", "toggle_minimap", "toggle_theme"],
            "Navigation": ["next_tab", "prev_tab", "switch_to_tab_1", "switch_to_tab_2", 
                          "switch_to_tab_3", "switch_to_tab_4", "switch_to_tab_5"],
            "Run": ["run_code", "compile_only", "stop_execution"]
        }
        
        # Loop through categories
        row = 0
        for category, cmd_ids in categories.items():
            # Add category header
            tk.Label(shortcuts_frame, text=category, font=("Arial", 12, "bold"), 
                     anchor="w").grid(row=row, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 5))
            row += 1
            
            # Add commands in this category
            for cmd in commands:
                if cmd["id"] in cmd_ids:
                    # Command name
                    tk.Label(shortcuts_frame, text=cmd["name"], anchor="w").grid(
                        row=row, column=0, sticky="w", padx=5, pady=2)
                    
                    # Current shortcut
                    shortcut_text = tk.StringVar(value=cmd["display_key"])
                    shortcut_label = tk.Label(
                        shortcuts_frame, 
                        textvariable=shortcut_text,
                        anchor="w", 
                        width=20,
                        relief="groove", 
                        padx=5
                    )
                    shortcut_label.grid(row=row, column=1, sticky="w", padx=5, pady=2)
                    
                    # Edit button
                    edit_btn = tk.Button(
                        shortcuts_frame, 
                        text="Change", 
                        command=lambda c=cmd, st=shortcut_text: self._edit_shortcut(c, st)
                    )
                    edit_btn.grid(row=row, column=2, sticky="w", padx=5, pady=2)
                    
                    row += 1
        
        # Update canvas scroll region
        shortcuts_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        
        # Button frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Reset defaults button
        reset_btn = tk.Button(
            button_frame, 
            text="Reset to Defaults", 
            command=self._reset_defaults
        )
        reset_btn.pack(side="left", padx=5)
        
        # Close button
        close_btn = tk.Button(
            button_frame, 
            text="Close", 
            command=self.dialog.destroy
        )
        close_btn.pack(side="right", padx=5)
        
        # Bind dialog close event
        self.dialog.protocol("WM_DELETE_WINDOW", self.dialog.destroy)
    
    def _edit_shortcut(self, command, shortcut_text_var):
        """
        Show a dialog to edit a keyboard shortcut
        
        Args:
            command: Command information dictionary
            shortcut_text_var: StringVar for displaying the shortcut
        """
        # Create dialog
        edit_dialog = tk.Toplevel(self.dialog)
        edit_dialog.title("Edit Shortcut")
        edit_dialog.geometry("400x150")
        edit_dialog.transient(self.dialog)
        edit_dialog.grab_set()
        
        # Center on parent
        x = self.dialog.winfo_rootx() + (self.dialog.winfo_width() // 2) - 200
        y = self.dialog.winfo_rooty() + (self.dialog.winfo_height() // 2) - 75
        edit_dialog.geometry(f"+{x}+{y}")
        
        # Create widgets
        tk.Label(
            edit_dialog, 
            text=f"Press the key combination for '{command['name']}':", 
            font=("Arial", 10, "bold")
        ).pack(pady=(20, 10))
        
        new_key_var = tk.StringVar(value="Press a key combination...")
        key_label = tk.Label(
            edit_dialog, 
            textvariable=new_key_var,
            font=("Arial", 12),
            relief="groove", 
            padding=10
        )
        key_label.pack(pady=10)
        
        # Focus the dialog to capture keys
        edit_dialog.focus_force()
        
        # Key event handler
        def on_key(event):
            # Convert event to binding string
            key = ""
            if event.state & 0x4:  # Control
                key += "Control-"
            if event.state & 0x8:  # Alt
                key += "Alt-"
            if event.state & 0x1:  # Shift
                key += "Shift-"
            
            # Add the key itself
            if event.keysym in ('Control_L', 'Control_R', 'Alt_L', 'Alt_R', 
                               'Shift_L', 'Shift_R'):
                # Ignore modifier key events
                return
            
            key += event.keysym.lower()
            
            # Format for display
            binding = f"<{key}>"
            display_key = self.keybindings.get_key_display_text(binding)
            
            # Update label
            new_key_var.set(display_key)
            
            # Store for saving
            edit_dialog.user_key = binding
        
        # Button frame
        button_frame = tk.Frame(edit_dialog)
        button_frame.pack(fill="x", pady=(10, 0), padx=10)
        
        # Cancel button
        cancel_btn = tk.Button(
            button_frame, 
            text="Cancel", 
            command=edit_dialog.destroy
        )
        cancel_btn.pack(side="left", padx=5)
        
        # Clear button
        clear_btn = tk.Button(
            button_frame, 
            text="Clear", 
            command=lambda: new_key_var.set("No shortcut")
        )
        clear_btn.pack(side="left", padx=5)
        
        # Save button
        def save_key():
            if hasattr(edit_dialog, "user_key"):
                # Update keybinding
                self.keybindings.set_binding(command["id"], edit_dialog.user_key)
                
                # Update display
                display_key = self.keybindings.get_key_display_text(edit_dialog.user_key)
                shortcut_text_var.set(display_key)
                
                # Save to file
                self.keybindings.save_to_file("keybindings.json")
            edit_dialog.destroy()
        
        save_btn = tk.Button(
            button_frame, 
            text="Save", 
            command=save_key
        )
        save_btn.pack(side="right", padx=5)
        
        # Bind key event
        edit_dialog.bind("<Key>", on_key)
    
    def _reset_defaults(self):
        """Reset all keybindings to default values"""
        # Confirm with user
        confirm = tk.messagebox.askyesno(
            "Reset Shortcuts",
            "Are you sure you want to reset all keyboard shortcuts to their default values?",
            parent=self.dialog
        )
        
        if confirm:
            # Reset the bindings
            self.keybindings.reset_to_defaults()
            
            # Save to file
            self.keybindings.save_to_file("keybindings.json")
            
            # Close and reopen dialog to refresh
            self.dialog.destroy()
            self.dialog = None
            self.show()
