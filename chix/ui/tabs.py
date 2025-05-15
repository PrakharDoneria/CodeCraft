"""
Tab management for ChiX Editor
"""

import customtkinter as ctk
import tkinter as tk
import os
from chix.ui.widgets import EnhancedTextEditor, LineNumbers, TabButton, SearchReplaceBar
from chix.ui.minimap import Minimap
from chix.ui.theme import get_color
from chix.utils.highlighter import highlight_syntax
from chix.core.file_ops import save_file, save_file_as, save_to_temp, load_from_temp, clean_temp_files
import uuid

class TabView:
    """Tab view for managing multiple editor tabs"""
    
    def __init__(self, parent, state):
        self.parent = parent
        self.state = state
        self.tabs = {}  # {tab_id: {"editor": editor, "file_path": path, "modified": bool, "temp_id": uuid}}
        self.tab_counter = 0
        self.current_tab_id = None
        
        # Create main container
        self.frame = ctk.CTkFrame(parent)
        self.frame.pack(fill="both", expand=True)
        
        # Tab bar
        self.tab_bar = ctk.CTkFrame(self.frame, height=30, fg_color=get_color("bg_secondary"))
        self.tab_bar.pack(fill="x", side="top")
        
        # Create tab buttons container with scrolling support
        self.tab_buttons_frame = ctk.CTkFrame(self.tab_bar, fg_color="transparent")
        self.tab_buttons_frame.pack(side="left", fill="x", expand=True)
        
        # Tab buttons dictionary
        self.tab_buttons = {}
        
        # Editor container
        self.editor_container = ctk.CTkFrame(self.frame)
        self.editor_container.pack(fill="both", expand=True)
        
        # Current editor widgets
        self.current_editor_frame = None
        self.current_line_numbers = None
        self.current_editor = None
        self.current_minimap = None
        self.current_search_bar = None
        
        # Setup autosave
        self.autosave_interval = 60000  # 60 seconds (in milliseconds)
        self._setup_autosave()
        
        # Clean up old temp files on startup
        clean_temp_files()
        
    def _setup_autosave(self):
        """Set up the autosave timer"""
        self._autosave_all_tabs()
        self.parent.after(self.autosave_interval, self._setup_autosave)
    
    def _autosave_all_tabs(self):
        """Autosave all open tabs to temp files"""
        for tab_id, tab_data in self.tabs.items():
            if tab_data["modified"]:
                content = tab_data["editor"].get("1.0", "end-1c")
                temp_id = tab_data.get("temp_id")
                if not temp_id:
                    temp_id = str(uuid.uuid4())
                    tab_data["temp_id"] = temp_id
                save_to_temp(content, temp_id)
        
        # Create initial tab if needed
        if not self.tabs:
            self.create_tab()
    
    def create_tab(self, file_path=None, content=None):
        """Create a new editor tab"""
        tab_id = f"tab_{self.tab_counter}"
        self.tab_counter += 1
        
        # Calculate tab name
        tab_name = "untitled"
        if file_path:
            tab_name = os.path.basename(file_path)
        
        # Create tab button
        tab_button = TabButton(
            self.tab_buttons_frame,
            tab_id=tab_id,
            text=tab_name,
            on_select=lambda id=tab_id: self.select_tab(id),
            on_close=lambda id=tab_id: self.close_tab(id),
            width=120,
            height=28
        )
        
        # Set callbacks for tab button context menu
        tab_button._close_others_callback = self.close_other_tabs
        tab_button._close_all_callback = self.close_all_tabs
        
        tab_button.pack(side="left", padx=(0, 1), pady=0)
        self.tab_buttons[tab_id] = tab_button
        
        # Create editor frame (but don't display it yet)
        editor_frame = ctk.CTkFrame(self.editor_container)
        
        # Create editor with line numbers and minimap in the frame
        editor_with_guides_frame = ctk.CTkFrame(editor_frame, fg_color="transparent")
        editor_with_guides_frame.pack(fill="both", expand=True)
        
        # Create the editor first
        editor = EnhancedTextEditor(editor_with_guides_frame, self.state)
        editor.pack(side="left", fill="both", expand=True)
        
        # Then create line numbers with the editor
        line_numbers = LineNumbers(editor_with_guides_frame, editor._textbox)
        line_numbers.pack(side="left", fill="y")
        
        # Add minimap if enabled
        minimap = None
        if self.state.get("show_minimap", True):
            minimap = Minimap(editor_with_guides_frame, editor)
            minimap.pack(side="right", fill="y", padx=(2, 0))
        
        # Create a hidden search bar
        search_bar = SearchReplaceBar(editor_frame, editor)
        # It will be packed when needed
        
        # Set callback functions
        editor.on_save = lambda: self.save_tab(tab_id)
        editor.on_find = lambda: self.show_find_replace_for_tab(tab_id)
        
        # Add a change callback to update modified status
        def on_change():
            self.mark_tab_modified(tab_id)
        editor.on_text_changed = on_change
        
        # Initialize content if provided
        if content:
            editor.delete("1.0", "end")
            editor.insert("1.0", content)
            highlight_syntax(editor)
        elif file_path and os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                    editor.delete("1.0", "end")
                    editor.insert("1.0", content)
                    highlight_syntax(editor)
            except Exception as e:
                # Insert error message
                editor.insert("1.0", f"# Error loading file: {str(e)}\n\n")
        
        # Generate a unique ID for temp files
        temp_id = str(uuid.uuid4())
        
        # Store tab information
        self.tabs[tab_id] = {
            "editor": editor,
            "editor_frame": editor_frame,
            "line_numbers": line_numbers,
            "file_path": file_path,
            "modified": False,
            "minimap": minimap,
            "search_bar": search_bar,
            "temp_id": temp_id
        }
        
        # If content was provided but no file path, save to temp immediately
        if content and not file_path:
            save_to_temp(content, temp_id)
        
        # Select the new tab
        self.select_tab(tab_id)
        return tab_id
    
    def select_tab(self, tab_id):
        """Select a tab by its ID"""
        if tab_id not in self.tabs:
            return
        
        # Hide current editor if any
        if self.current_editor_frame:
            self.current_editor_frame.pack_forget()
        
        # Get tab data
        tab_data = self.tabs[tab_id]
        
        # Show the selected editor
        tab_data["editor_frame"].pack(fill="both", expand=True)
        
        # Update current references
        self.current_editor_frame = tab_data["editor_frame"]
        self.current_editor = tab_data["editor"]
        self.current_line_numbers = tab_data["line_numbers"]
        self.current_minimap = tab_data["minimap"]
        self.current_search_bar = tab_data["search_bar"]
        
        # Update tab buttons
        for tid, button in self.tab_buttons.items():
            button.set_active(tid == tab_id)
        
        # Update current tab id
        self.current_tab_id = tab_id
        
        # Update state
        self.state["active_editor"] = self.current_editor
        self.state["current_file"] = tab_data["file_path"]
        
        # Update status bar
        if "status_bar" in self.state:
            self.state["status_bar"].update_file_info(
                tab_data["file_path"] if tab_data["file_path"] else "Untitled"
            )
        
        # Give focus to the editor
        self.current_editor.focus_set()
    
    def close_tab(self, tab_id):
        """Close a tab by its ID"""
        if tab_id not in self.tabs:
            return
        
        # Check if tab has unsaved changes
        if self.tabs[tab_id]["modified"]:
            # Ask user to save changes
            result = ctk.CTkInputDialog(
                text=f"Save changes to {os.path.basename(self.tabs[tab_id]['file_path'] or 'Untitled')}?",
                title="Unsaved Changes"
            ).get_input()
            
            if result and result.lower() in ["y", "yes"]:
                self.save_tab(tab_id)
        
        # Remove tab button
        if tab_id in self.tab_buttons:
            self.tab_buttons[tab_id].destroy()
            del self.tab_buttons[tab_id]
        
        # Store temp references
        tab_data = self.tabs[tab_id]
        is_current = (tab_id == self.current_tab_id)
        
        # Remove tab data
        del self.tabs[tab_id]
        
        # If we closed the current tab, select another one
        if is_current:
            # Find a tab to select
            if self.tabs:
                next_tab_id = list(self.tabs.keys())[0]
                self.select_tab(next_tab_id)
            else:
                # No tabs left, clear references
                self.current_tab_id = None
                self.current_editor_frame = None
                self.current_editor = None
                self.state["active_editor"] = None
                self.state["current_file"] = None
                
                # Create a new empty tab
                self.create_tab()
    
    def close_other_tabs(self, keep_tab_id):
        """Close all tabs except the specified one"""
        for tab_id in list(self.tabs.keys()):
            if tab_id != keep_tab_id:
                self.close_tab(tab_id)
    
    def close_all_tabs(self):
        """Close all tabs"""
        for tab_id in list(self.tabs.keys()):
            self.close_tab(tab_id)
    
    def get_current_editor(self):
        """Get the current editor widget"""
        return self.current_editor
    
    def get_current_file_path(self):
        """Get the file path of the current tab"""
        if self.current_tab_id and self.current_tab_id in self.tabs:
            return self.tabs[self.current_tab_id]["file_path"]
        return None
    
    def open_file(self, file_path):
        """Open a file in a new tab or existing tab if already open"""
        # Check if file is already open
        for tab_id, tab_data in self.tabs.items():
            if tab_data["file_path"] == file_path:
                self.select_tab(tab_id)
                return tab_id
        
        # Not open, create new tab
        return self.create_tab(file_path=file_path)
    
    def save_tab(self, tab_id):
        """Save the content of a tab"""
        if tab_id not in self.tabs:
            return False
        
        tab_data = self.tabs[tab_id]
        content = tab_data["editor"].get("1.0", "end-1c")
        
        if tab_data["file_path"]:
            # Save to existing file
            try:
                with open(tab_data["file_path"], "w") as f:
                    f.write(content)
                
                # Mark as not modified
                self.mark_tab_modified(tab_id, modified=False)
                
                # Update status bar
                if "status_bar" in self.state:
                    self.state["status_bar"].set_message(f"Saved {os.path.basename(tab_data['file_path'])}")
                
                return True
            except Exception as e:
                if "status_bar" in self.state:
                    self.state["status_bar"].set_message(f"Error saving: {str(e)}")
                return False
        else:
            # No file path, use save as
            return self.save_tab_as(tab_id)
    
    def save_tab_as(self, tab_id):
        """Save the content of a tab with a new filename"""
        if tab_id not in self.tabs:
            return False
        
        tab_data = self.tabs[tab_id]
        content = tab_data["editor"].get("1.0", "end-1c")
        
        # Get current file path if any
        current_file_path = tab_data["file_path"]
        
        # Initialize file_path with the current path for the dialog
        file_path = save_file_as(self.state, 
                                 editor=tab_data["editor"], 
                                 file_path=current_file_path)
        
        if file_path:
            # Update tab with new path
            tab_data["file_path"] = file_path
            
            # Update tab button text
            tab_name = os.path.basename(file_path)
            self.tab_buttons[tab_id].original_text = tab_name
            self.tab_buttons[tab_id].configure(text=tab_name)
            
            # Mark as not modified
            self.mark_tab_modified(tab_id, modified=False)
            
            # Update status bar
            if "status_bar" in self.state:
                self.state["status_bar"].set_message(f"Saved as {tab_name}")
                self.state["status_bar"].update_file_info(file_path)
            
            # Update app state
            if tab_id == self.current_tab_id:
                self.state["current_file"] = file_path
            
            return True
        
        return False
    
    def save_current_tab(self):
        """Save the current tab"""
        if self.current_tab_id:
            return self.save_tab(self.current_tab_id)
        return False
    
    def save_current_tab_as(self):
        """Save the current tab with a new filename"""
        if self.current_tab_id:
            return self.save_tab_as(self.current_tab_id)
        return False
    
    def save_all_tabs(self):
        """Save all tabs"""
        results = []
        for tab_id in self.tabs:
            results.append(self.save_tab(tab_id))
        return all(results)
    
    def mark_tab_modified(self, tab_id, modified=True):
        """Mark a tab as modified or unmodified"""
        if tab_id not in self.tabs:
            return
        
        # Update tab data
        self.tabs[tab_id]["modified"] = modified
        
        # Update tab button
        if tab_id in self.tab_buttons:
            self.tab_buttons[tab_id].mark_modified(modified)
    
    def show_find_replace(self):
        """Show the find and replace dialog for the current tab"""
        if self.current_tab_id:
            self.show_find_replace_for_tab(self.current_tab_id)
    
    def show_find_replace_for_tab(self, tab_id):
        """Show the find and replace dialog for a specific tab"""
        if tab_id not in self.tabs:
            return
        
        search_bar = self.tabs[tab_id]["search_bar"]
        search_bar.show()
    
    def next_tab(self):
        """Switch to the next tab"""
        if not self.tabs:
            return
            
        # Get sorted tab IDs
        tab_ids = sorted(self.tabs.keys())
        
        if self.current_tab_id not in tab_ids:
            # Just select the first tab
            self.select_tab(tab_ids[0])
            return
            
        # Find current index
        current_index = tab_ids.index(self.current_tab_id)
        
        # Calculate next index
        next_index = (current_index + 1) % len(tab_ids)
        
        # Select the next tab
        self.select_tab(tab_ids[next_index])
    
    def prev_tab(self):
        """Switch to the previous tab"""
        if not self.tabs:
            return
            
        # Get sorted tab IDs
        tab_ids = sorted(self.tabs.keys())
        
        if self.current_tab_id not in tab_ids:
            # Just select the first tab
            self.select_tab(tab_ids[0])
            return
            
        # Find current index
        current_index = tab_ids.index(self.current_tab_id)
        
        # Calculate previous index
        prev_index = (current_index - 1) % len(tab_ids)
        
        # Select the previous tab
        self.select_tab(tab_ids[prev_index])
    
    def has_unsaved_changes(self):
        """Check if any tabs have unsaved changes"""
        for tab_id, tab_data in self.tabs.items():
            if tab_data["modified"]:
                return True
        return False
    
    def set_minimap_visibility(self, visible):
        """Set the visibility of minimaps in all tabs"""
        for tab_id, tab_data in self.tabs.items():
            if tab_data["minimap"]:
                if visible:
                    tab_data["minimap"].pack(side="right", fill="y", padx=(2, 0))
                else:
                    tab_data["minimap"].pack_forget()
    
    def update_theme(self):
        """Update the appearance after theme change"""
        # Update tab bar
        self.tab_bar.configure(fg_color=get_color("bg_secondary"))
        
        # Update editor frames
        for tab_id, tab_data in self.tabs.items():
            # Update editor appearance
            editor = tab_data["editor"]
            editor._textbox.configure(bg=get_color("bg_primary"), fg=get_color("fg_primary"))
            editor._setup_tags()  # Refresh syntax highlighting tags
            
            # Reapply syntax highlighting
            highlight_syntax(editor)
            
            # Update line numbers
            line_numbers = tab_data["line_numbers"]
            line_numbers.configure(bg=get_color("bg_secondary"))
            line_numbers.text_color = get_color("fg_secondary")
            line_numbers.redraw()
            
            # Update minimap if present
            if tab_data["minimap"]:
                tab_data["minimap"].update_theme()
            
            # Update tab buttons
            if tab_id in self.tab_buttons:
                button = self.tab_buttons[tab_id]
                if button.is_active:
                    button.configure(
                        fg_color=get_color("bg_primary"),
                        text_color=get_color("accent_primary")
                    )
                else:
                    button.configure(
                        fg_color=get_color("bg_secondary"),
                        text_color=get_color("fg_primary")
                    )
    
    def pack(self, **kwargs):
        """Pack the tab view"""
        self.frame.pack(**kwargs)
