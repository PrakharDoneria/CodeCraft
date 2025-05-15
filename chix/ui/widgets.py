"""
Custom widgets for ChiX Editor
"""

import customtkinter as ctk
import tkinter as tk
from chix.ui.theme import get_theme, get_color
from chix.utils.highlighter import highlight_syntax
import webbrowser
import re

class LineNumbers(ctk.CTkCanvas):
    """Line numbers widget for editor"""
    
    def __init__(self, parent, text_widget, **kwargs):
        # Initialize with proper tkinter parameters
        bg_color = get_color("bg_secondary")
        if "bg_color" in kwargs:
            kwargs.pop("bg_color")
        
        super().__init__(parent, width=50, bg=bg_color, highlightthickness=0, **kwargs)
        self.text_widget = text_widget
        
        # Font configuration - initialize before calling redraw()
        self.font = ("Cascadia Code", 12)
        self.text_color = get_color("fg_secondary")
        
        # Bind events if text_widget is provided
        if self.text_widget is not None:
            self.text_widget.bind('<KeyRelease>', self.redraw)
            self.text_widget.bind('<ButtonRelease-1>', self.redraw)
            self.text_widget.bind('<MouseWheel>', self.redraw)
            self.text_widget.bind('<Configure>', self.redraw)
            
            # Draw initial line numbers
            self.redraw()
    
    def redraw(self, event=None):
        """Redraw line numbers"""
        self.delete("all")
        
        # Return if text_widget is None
        if self.text_widget is None:
            # Just draw background
            self.create_rectangle(0, 0, self.winfo_width(), self.winfo_height(), 
                                  fill=get_color("bg_secondary"), outline="")
            return
        
        # Get total lines
        line_count = int(self.text_widget.index('end-1c').split('.')[0])
        
        # Create background
        self.create_rectangle(0, 0, self.winfo_width(), self.winfo_height(), 
                              fill=get_color("bg_secondary"), outline="")
        
        # Current line highlight
        current_line = int(self.text_widget.index(tk.INSERT).split('.')[0])
        
        for i in range(1, line_count + 1):
            y_coord = self.text_widget.dlineinfo(f"{i}.0")
            if y_coord:
                # Highlight current line
                if i == current_line:
                    text_color = get_color("accent_primary")
                    font_weight = "bold"
                else:
                    text_color = self.text_color
                    font_weight = "normal"
                
                self.create_text(
                    self.winfo_width() - 10, 
                    y_coord[1] + 8,  # Centered vertically in line
                    text=str(i), 
                    fill=text_color, 
                    font=(self.font[0], self.font[1], font_weight),
                    anchor="e"  # Right-aligned
                )

class EnhancedTextEditor(ctk.CTkTextbox):
    """Enhanced text editor with advanced features"""
    
    def __init__(self, master, state, **kwargs):
        # Apply theme colors
        theme = get_theme()
        self.tab_size = state.get("tab_size", 4)
        
        super().__init__(
            master, 
            font=("Cascadia Code", 14),
            fg_color=theme["bg_primary"],
            text_color=theme["fg_primary"],
            border_width=0,
            corner_radius=0,
            wrap="none",
            **kwargs
        )
        
        self.state = state
        self._setup_events()
        self._setup_tags()
        self._setup_undo_redo()
        
        # Track syntax errors
        self.error_lines = set()
        
        # Last position for context menu
        self.last_click_pos = "1.0"
    
    def _setup_events(self):
        """Set up event bindings"""
        # Basic editing functionality
        self.bind('<Tab>', self._handle_tab)
        self.bind('<Return>', self._handle_enter)
        self.bind('<BackSpace>', self._handle_backspace)
        self.bind('<Control-a>', self._handle_select_all)
        
        # Bracket completion
        self.bind('(', lambda e: self._auto_close_bracket('(', ')'))
        self.bind('[', lambda e: self._auto_close_bracket('[', ']'))
        self.bind('{', lambda e: self._auto_close_bracket('{', '}'))
        self.bind('"', lambda e: self._auto_close_bracket('"', '"'))
        self.bind("'", lambda e: self._auto_close_bracket("'", "'"))
        
        # Save functionality
        self.bind('<Control-s>', self._handle_save)
        
        # Find functionality
        self.bind('<Control-f>', self._handle_find)
        
        # Context menu
        self.bind('<Button-3>', self._show_context_menu)
        
        # Track changes
        self.bind('<KeyRelease>', self._on_text_changed)
    
    def _setup_tags(self):
        """Set up text tags for syntax highlighting"""
        text_widget = self._textbox
        
        # Configure standard syntax highlighting tags
        text_widget.tag_configure("keyword", foreground=get_color("keyword"))
        text_widget.tag_configure("string", foreground=get_color("string"))
        text_widget.tag_configure("comment", foreground=get_color("comment"))
        text_widget.tag_configure("function", foreground=get_color("function"))
        text_widget.tag_configure("preprocessor", foreground=get_color("type"))
        text_widget.tag_configure("type", foreground=get_color("type"))
        text_widget.tag_configure("number", foreground=get_color("number"))
        text_widget.tag_configure("operator", foreground=get_color("operator"))
        text_widget.tag_configure("error", foreground=get_color("error"), underline=1)
        
        # Selection and cursor line highlighting
        text_widget.tag_configure("current_line", background=get_color("line_highlight"))
        
        # Bracket matching
        text_widget.tag_configure("matching_bracket", background=get_color("selection"))
    
    def _setup_undo_redo(self):
        """Set up the undo/redo stack"""
        self._textbox.configure(undo=True, maxundo=100)
    
    def _handle_tab(self, event):
        """Handle tab key press - insert spaces"""
        self.insert(tk.INSERT, " " * self.tab_size)
        return "break"
    
    def _handle_enter(self, event):
        """Handle Enter key press - auto-indent"""
        # Get the current line
        line = self.get("insert linestart", "insert lineend")
        
        # Calculate the indentation level (count leading spaces)
        indent_match = re.match(r"^(\s+)", line)
        indent = indent_match.group(1) if indent_match else ""
        
        # Check if we need to add additional indentation
        if line.endswith('{'):
            indent += " " * self.tab_size
        
        # Insert new line with proper indentation
        self.insert(tk.INSERT, f"\n{indent}")
        return "break"
    
    def _handle_backspace(self, event):
        """Handle backspace to implement smart tab removal"""
        # Get current cursor position and the character before
        current_pos = self.index(tk.INSERT)
        line, col = map(int, current_pos.split('.'))
        
        # If we're at the beginning of a line, do standard backspace
        if col == 0:
            return
        
        # Check if there are spaces before cursor that match tab width
        if col >= self.tab_size:
            # Get the text before the cursor on this line
            before_text = self.get(f"{line}.{col-self.tab_size}", f"{line}.{col}")
            # If it's all spaces, delete the whole tab width
            if before_text == " " * self.tab_size:
                self.delete(f"{line}.{col-self.tab_size}", f"{line}.{col}")
                return "break"
        
        # Otherwise, do standard backspace
        return
    
    def _handle_select_all(self, event):
        """Handle Ctrl+A to select all text"""
        self.tag_add(tk.SEL, "1.0", tk.END)
        self.mark_set(tk.INSERT, "1.0")
        self.see(tk.INSERT)
        return "break"
    
    def _handle_save(self, event):
        """Handle Ctrl+S to save file"""
        if hasattr(self, "on_save") and callable(self.on_save):
            self.on_save()
        return "break"
    
    def _handle_find(self, event):
        """Handle Ctrl+F to find text"""
        if hasattr(self, "on_find") and callable(self.on_find):
            self.on_find()
        return "break"
    
    def _auto_close_bracket(self, opening, closing):
        """Automatically add closing bracket after opening bracket"""
        # Get current selection
        try:
            selection = self.selection_get()
            # If text is selected, surround with brackets
            self.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.insert(tk.INSERT, opening + selection + closing)
            return "break"
        except:
            # No selection, just add both brackets and place cursor between them
            self.insert(tk.INSERT, opening + closing)
            self.mark_set(tk.INSERT, f"insert-{len(closing)}c")
            return "break"
    
    def _on_text_changed(self, event=None):
        """Handle text changes for syntax highlighting"""
        # Call the highlighting function
        highlight_syntax(self)
        
        # Highlight the current line
        self._highlight_current_line()
        
        # Update the document in the app state
        if hasattr(self, "on_text_changed") and callable(self.on_text_changed):
            self.on_text_changed()
    
    def _highlight_current_line(self):
        """Highlight the line where the cursor is located"""
        text_widget = self._textbox
        
        # Remove previous highlighting
        text_widget.tag_remove("current_line", "1.0", tk.END)
        
        # Add highlighting to current line
        current_line = text_widget.index(tk.INSERT).split('.')[0]
        text_widget.tag_add("current_line", f"{current_line}.0", f"{current_line}.end+1c")
        
        # Make sure current_line is below selection
        text_widget.tag_lower("current_line", tk.SEL)
    
    def _show_context_menu(self, event):
        """Show context menu on right-click"""
        self.last_click_pos = self.index(f"@{event.x},{event.y}")
        
        context_menu = tk.Menu(self, tearoff=0, bg=get_color("bg_secondary"), fg=get_color("fg_primary"))
        context_menu.add_command(label="Cut", command=lambda: self._cut())
        context_menu.add_command(label="Copy", command=lambda: self._copy())
        context_menu.add_command(label="Paste", command=lambda: self._paste())
        context_menu.add_separator()
        context_menu.add_command(label="Select All", command=lambda: self._select_all())
        context_menu.add_separator()
        context_menu.add_command(label="Undo", command=lambda: self._undo())
        context_menu.add_command(label="Redo", command=lambda: self._redo())
        
        # Position and display the menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            context_menu.grab_release()
        
        return "break"
    
    def _cut(self):
        """Cut selected text to clipboard"""
        self._copy()
        self.delete(tk.SEL_FIRST, tk.SEL_LAST)
    
    def _copy(self):
        """Copy selected text to clipboard"""
        try:
            self.clipboard_clear()
            text = self.selection_get()
            self.clipboard_append(text)
        except:
            pass
    
    def _paste(self):
        """Paste text from clipboard"""
        try:
            text = self.clipboard_get()
            # If there's a selection, replace it
            try:
                self.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except:
                pass
            self.insert(tk.INSERT, text)
            self._on_text_changed()
        except:
            pass
    
    def _select_all(self):
        """Select all text"""
        self.tag_add(tk.SEL, "1.0", tk.END)
        self.mark_set(tk.INSERT, "1.0")
        self.see(tk.INSERT)
    
    def _undo(self):
        """Undo last change"""
        try:
            self._textbox.edit_undo()
            self._on_text_changed()
        except:
            pass
    
    def _redo(self):
        """Redo last undone change"""
        try:
            self._textbox.edit_redo()
            self._on_text_changed()
        except:
            pass
    
    def mark_error(self, line, message="Syntax error"):
        """Mark a line as containing an error"""
        text_widget = self._textbox
        line = int(line)
        
        # Add line to error set
        self.error_lines.add(line)
        
        # Add error tag to line
        text_widget.tag_add("error", f"{line}.0", f"{line}.end")
        
        # Store error message for tooltip
        if not hasattr(self, "error_messages"):
            self.error_messages = {}
        self.error_messages[line] = message
    
    def clear_errors(self):
        """Clear all error markings"""
        text_widget = self._textbox
        text_widget.tag_remove("error", "1.0", tk.END)
        self.error_lines = set()
        if hasattr(self, "error_messages"):
            self.error_messages = {}

class ClickableLabel(ctk.CTkLabel):
    """Label that can be clicked to trigger a callback"""
    
    def __init__(self, master, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.command = command
        self.bind("<Button-1>", self._on_click)
        self.configure(cursor="hand2")
    
    def _on_click(self, event):
        """Handle click event"""
        if self.command:
            self.command()

class HyperlinkLabel(ctk.CTkLabel):
    """Label that functions as a hyperlink"""
    
    def __init__(self, master, url, **kwargs):
        super().__init__(master, **kwargs)
        self.url = url
        self.bind("<Button-1>", self._open_url)
        self.configure(cursor="hand2", text_color=get_color("accent_primary"))
    
    def _open_url(self, event):
        """Open URL in default browser"""
        webbrowser.open(self.url)

class ImageButton(ctk.CTkButton):
    """Button with SVG icon support"""
    
    def __init__(self, master, text="", icon=None, tooltip=None, **kwargs):
        super().__init__(master, text=text, **kwargs)
        
        if tooltip:
            self.tooltip_text = tooltip
            self.bind("<Enter>", self._show_tooltip)
            self.bind("<Leave>", self._hide_tooltip)
    
    def _show_tooltip(self, event):
        """Show tooltip when mouse hovers over button"""
        x, y, _, _ = self.bbox("insert")
        x += self.winfo_rootx() + 25
        y += self.winfo_rooty() + 25
        
        # Create a toplevel window
        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        # Create tooltip content
        label = tk.Label(self.tooltip, text=self.tooltip_text, justify="left",
                      background=get_color("bg_tertiary"), foreground=get_color("fg_primary"),
                      relief="solid", borderwidth=1, padx=5, pady=2)
        label.pack(ipadx=1)
    
    def _hide_tooltip(self, event):
        """Hide tooltip when mouse leaves button"""
        if hasattr(self, "tooltip"):
            self.tooltip.destroy()

class TabButton(ctk.CTkButton):
    """Button used for editor tabs"""
    
    def __init__(self, master, tab_id, text, on_select, on_close, **kwargs):
        super().__init__(
            master, 
            text=text,
            fg_color=get_color("bg_secondary"),
            hover_color=get_color("bg_hover"),
            corner_radius=0,
            border_width=0,
            **kwargs
        )
        
        self.tab_id = tab_id
        self.on_select = on_select
        self.on_close = on_close
        
        # Store original text for reference
        self.original_text = text
        
        # Modified indicator
        self.is_modified = False
        
        # Active state
        self.is_active = False
        
        # Configure events
        self.configure(command=self._select_tab)
        
        # Add X button for closing
        self.bind("<Button-3>", self._show_context_menu)
    
    def _select_tab(self):
        """Handler for tab selection"""
        if self.on_select:
            self.on_select(self.tab_id)
    
    def mark_modified(self, modified=True):
        """Mark tab as modified with an asterisk"""
        self.is_modified = modified
        
        if modified and not self.text.endswith("*"):
            self.configure(text=f"{self.original_text}*")
        elif not modified and self.text.endswith("*"):
            self.configure(text=self.original_text)
    
    def set_active(self, active=True):
        """Set the active state of the tab"""
        self.is_active = active
        
        if active:
            self.configure(
                fg_color=get_color("bg_primary"),
                text_color=get_color("accent_primary")
            )
        else:
            self.configure(
                fg_color=get_color("bg_secondary"),
                text_color=get_color("fg_primary")
            )
    
    def _show_context_menu(self, event):
        """Show context menu on right-click"""
        context_menu = tk.Menu(self, tearoff=0, bg=get_color("bg_secondary"), fg=get_color("fg_primary"))
        context_menu.add_command(label="Close", command=self._close_tab)
        context_menu.add_command(label="Close Others", command=self._close_other_tabs)
        context_menu.add_command(label="Close All", command=self._close_all_tabs)
        
        # Position and display the menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            context_menu.grab_release()
    
    def _close_tab(self):
        """Close this tab"""
        if self.on_close:
            self.on_close(self.tab_id)
    
    def _close_other_tabs(self):
        """Close all tabs except this one"""
        if hasattr(self, "_close_others_callback") and self._close_others_callback:
            self._close_others_callback(self.tab_id)
    
    def _close_all_tabs(self):
        """Close all tabs"""
        if hasattr(self, "_close_all_callback") and self._close_all_callback:
            self._close_all_callback()

class ToolbarButton(ctk.CTkButton):
    """Button used in toolbars"""
    
    def __init__(self, master, text="", icon_text=None, tooltip=None, **kwargs):
        # If an icon is provided, prepend it to the text
        display_text = f"{icon_text} {text}" if icon_text else text
        
        # Set default values if not provided in kwargs
        if 'fg_color' not in kwargs:
            kwargs['fg_color'] = get_color("bg_tertiary")
        if 'hover_color' not in kwargs:
            kwargs['hover_color'] = get_color("bg_hover")
        if 'corner_radius' not in kwargs:
            kwargs['corner_radius'] = 4
            
        super().__init__(
            master, 
            text=display_text.strip(),
            **kwargs
        )
        
        if tooltip:
            self.tooltip_text = tooltip
            self.bind("<Enter>", self._show_tooltip)
            self.bind("<Leave>", self._hide_tooltip)
    
    def _show_tooltip(self, event):
        """Show tooltip when mouse hovers over button"""
        x, y, _, _ = self.bbox("insert")
        x += self.winfo_rootx() + 25
        y += self.winfo_rooty() + 25
        
        # Create a toplevel window
        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        # Create tooltip content
        label = tk.Label(self.tooltip, text=self.tooltip_text, justify="left",
                      background=get_color("bg_tertiary"), foreground=get_color("fg_primary"),
                      relief="solid", borderwidth=1, padx=5, pady=2)
        label.pack(ipadx=1)
    
    def _hide_tooltip(self, event):
        """Hide tooltip when mouse leaves button"""
        if hasattr(self, "tooltip"):
            self.tooltip.destroy()

class SearchReplaceBar(ctk.CTkFrame):
    """Search and replace bar widget"""
    
    def __init__(self, master, editor, **kwargs):
        super().__init__(master, **kwargs)
        
        self.editor = editor
        self.matches = []
        self.current_match = -1
        
        # Create layout
        self._create_widgets()
        
        # Key bindings
        self.bind("<Escape>", self.hide)
        
    def _create_widgets(self):
        """Create the search and replace widgets"""
        # Main container with padding
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=10, pady=5)
        
        # Search row
        search_frame = ctk.CTkFrame(container, fg_color="transparent")
        search_frame.pack(fill="x")
        
        # Search label
        ctk.CTkLabel(search_frame, text="Find:", width=50).pack(side="left", padx=5)
        
        # Search entry
        self.search_entry = ctk.CTkEntry(search_frame, width=200)
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self._on_search_text_changed)
        self.search_entry.bind("<Return>", lambda e: self.find_next())
        
        # Search buttons
        btn_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        self.case_sensitive_var = tk.BooleanVar(value=False)
        case_check = ctk.CTkCheckBox(
            btn_frame, 
            text="Match case", 
            variable=self.case_sensitive_var,
            command=self._on_search_text_changed
        )
        case_check.pack(side="left", padx=5)
        
        self.regex_var = tk.BooleanVar(value=False)
        regex_check = ctk.CTkCheckBox(
            btn_frame, 
            text="Regex", 
            variable=self.regex_var,
            command=self._on_search_text_changed
        )
        regex_check.pack(side="left", padx=5)
        
        # Find buttons
        ctk.CTkButton(
            btn_frame, 
            text="Previous", 
            command=self.find_prev,
            width=80
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame, 
            text="Next", 
            command=self.find_next,
            width=80
        ).pack(side="left", padx=5)
        
        # Replace row
        replace_frame = ctk.CTkFrame(container, fg_color="transparent")
        replace_frame.pack(fill="x", pady=(5, 0))
        
        # Replace label
        ctk.CTkLabel(replace_frame, text="Replace:", width=50).pack(side="left", padx=5)
        
        # Replace entry
        self.replace_entry = ctk.CTkEntry(replace_frame, width=200)
        self.replace_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # Replace buttons
        btn_frame2 = ctk.CTkFrame(replace_frame, fg_color="transparent")
        btn_frame2.pack(side="right")
        
        ctk.CTkButton(
            btn_frame2, 
            text="Replace", 
            command=self.replace_current,
            width=80
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame2, 
            text="Replace All", 
            command=self.replace_all,
            width=80
        ).pack(side="left", padx=5)
        
        # Close button (X)
        ctk.CTkButton(
            container, 
            text="✕", 
            command=self.hide,
            width=20, 
            height=20,
            corner_radius=10,
            fg_color=get_color("bg_hover")
        ).place(relx=1.0, y=0, anchor="ne")
    
    def _on_search_text_changed(self, event=None):
        """Handle search text changes"""
        self.find_all()
        
        # If we have matches, go to the first one
        if self.matches and len(self.matches) > 0:
            self.current_match = 0
            self._highlight_current_match()
    
    def find_all(self):
        """Find all matches of search text in editor"""
        search_text = self.search_entry.get()
        if not search_text:
            self._clear_all_highlights()
            self.matches = []
            return
        
        # Get editor content
        content = self.editor.get("1.0", "end-1c")
        
        # Find all matches
        self.matches = []
        case_sensitive = self.case_sensitive_var.get()
        use_regex = self.regex_var.get()
        
        if use_regex:
            try:
                if case_sensitive:
                    pattern = re.compile(search_text)
                else:
                    pattern = re.compile(search_text, re.IGNORECASE)
                
                for match in pattern.finditer(content):
                    start_pos = self._get_text_position(content, match.start())
                    end_pos = self._get_text_position(content, match.end())
                    self.matches.append((start_pos, end_pos))
            except re.error:
                # Invalid regex, don't search
                pass
        else:
            # Simple string search
            if not case_sensitive:
                search_text = search_text.lower()
                search_content = content.lower()
            else:
                search_content = content
            
            start = 0
            while True:
                start = search_content.find(search_text, start)
                if start == -1:
                    break
                    
                end = start + len(search_text)
                start_pos = self._get_text_position(content, start)
                end_pos = self._get_text_position(content, end)
                self.matches.append((start_pos, end_pos))
                start = end
        
        # Highlight all matches
        self._clear_all_highlights()
        self._highlight_all_matches()
        
        # Update status with match count
        if hasattr(self.editor, "state") and "status_bar" in self.editor.state:
            count = len(self.matches)
            if count > 0:
                self.editor.state["status_bar"].set_message(f"{count} matches found")
            else:
                self.editor.state["status_bar"].set_message("No matches found")
    
    def _get_text_position(self, text, index):
        """Convert character index to 'line.column' position"""
        lines = text[:index].split("\n")
        line = len(lines)
        col = len(lines[-1])
        return f"{line}.{col}"
    
    def _highlight_all_matches(self):
        """Highlight all found matches"""
        text_widget = self.editor._textbox
        for i, (start, end) in enumerate(self.matches):
            text_widget.tag_add(f"search{i}", start, end)
            text_widget.tag_configure(f"search{i}", background=get_color("selection"))
    
    def _highlight_current_match(self):
        """Highlight current match with different color"""
        if not self.matches or self.current_match < 0 or self.current_match >= len(self.matches):
            return
            
        text_widget = self.editor._textbox
        
        # Highlight current match
        start, end = self.matches[self.current_match]
        
        # Remove current highlight from all matches
        for i in range(len(self.matches)):
            text_widget.tag_configure(f"search{i}", background=get_color("selection"))
        
        # Highlight current match
        text_widget.tag_configure(f"search{self.current_match}", background=get_color("accent_secondary"))
        
        # Ensure visible
        self.editor.see(start)
        
        # Move cursor to end of match
        self.editor.mark_set(tk.INSERT, end)
    
    def _clear_all_highlights(self):
        """Clear all search highlights"""
        text_widget = self.editor._textbox
        for tag in text_widget.tag_names():
            if tag.startswith("search"):
                text_widget.tag_delete(tag)
    
    def find_next(self):
        """Find the next occurrence of the search text"""
        if not self.matches:
            self.find_all()
            if not self.matches:
                return
        
        if self.current_match < len(self.matches) - 1:
            self.current_match += 1
        else:
            self.current_match = 0
            
        self._highlight_current_match()
    
    def find_prev(self):
        """Find the previous occurrence of the search text"""
        if not self.matches:
            self.find_all()
            if not self.matches:
                return
        
        if self.current_match > 0:
            self.current_match -= 1
        else:
            self.current_match = len(self.matches) - 1
            
        self._highlight_current_match()
    
    def replace_current(self):
        """Replace the current match with the replacement text"""
        if not self.matches or self.current_match < 0 or self.current_match >= len(self.matches):
            return
            
        replace_text = self.replace_entry.get()
        start, end = self.matches[self.current_match]
        
        # Replace the text
        self.editor.delete(start, end)
        self.editor.insert(start, replace_text)
        
        # Find all again to update matches
        self.find_all()
        
        # Stay at current match if possible
        if self.current_match >= len(self.matches):
            self.current_match = max(0, len(self.matches) - 1)
            
        if self.matches:
            self._highlight_current_match()
    
    def replace_all(self):
        """Replace all matches with the replacement text"""
        if not self.matches:
            return
            
        replace_text = self.replace_entry.get()
        
        # Need to replace from end to beginning to maintain positions
        for start, end in reversed(self.matches):
            self.editor.delete(start, end)
            self.editor.insert(start, replace_text)
        
        # Find all again to update matches
        self.find_all()
    
    def show(self):
        """Show the search and replace bar"""
        self.pack(fill="x", side="top", pady=(0, 5))
        
        # Focus the search entry
        self.search_entry.focus_set()
        
        # Select search text if any
        try:
            selection = self.editor.selection_get()
            self.search_entry.delete(0, "end")
            self.search_entry.insert(0, selection)
            self._on_search_text_changed()
        except:
            pass
    
    def hide(self, event=None):
        """Hide the search and replace bar"""
        self._clear_all_highlights()
        self.pack_forget()
        
        # Return focus to editor
        self.editor.focus_set()

# Toolbar separator widget
class ToolbarSeparator(ctk.CTkFrame):
    """Visual separator for toolbars"""
    
    def __init__(self, master, **kwargs):
        super().__init__(
            master, 
            width=2, 
            height=24, 
            fg_color=get_color("bg_hover"),
            **kwargs
        )
