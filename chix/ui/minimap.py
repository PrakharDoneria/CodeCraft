"""
Minimap implementation for code overview
"""

import customtkinter as ctk
import tkinter as tk
from chix.ui.theme import get_color
import re

class Minimap(ctk.CTkCanvas):
    """
    Minimap widget showing a small version of the code for navigation
    """
    
    def __init__(self, parent, editor, **kwargs):
        # Initialize with proper parameters
        super().__init__(
            parent, 
            width=100, 
            bg=get_color("bg_secondary"),
            highlightthickness=0,
            **kwargs
        )
        
        self.editor = editor
        self.scale_factor = 0.3  # Scale of the minimap text
        self.width = 100  # Width of the minimap
        
        # Bind events
        self.editor.bind("<KeyRelease>", self.update_minimap)
        self.editor.bind("<ButtonRelease-1>", self.update_minimap)
        self.editor.bind("<MouseWheel>", self.update_minimap)
        
        # Bind minimap click event to jump to position
        self.bind("<Button-1>", self.on_minimap_click)
        self.bind("<B1-Motion>", self.on_minimap_drag)
        
        # Initial update
        self.update_minimap()
    
    def update_minimap(self, event=None):
        """Update the minimap content"""
        self.delete("all")
        
        # Create background
        self.create_rectangle(
            0, 0, self.width, self.winfo_height(),
            fill=get_color("bg_secondary"),
            outline=""
        )
        
        # Get editor content
        content = self.editor.get("1.0", "end-1c")
        lines = content.split("\n")
        
        # Calculate line height in minimap
        line_height = max(1, int(14 * self.scale_factor))  # Based on font size
        
        # Draw content lines
        y_pos = 0
        for i, line in enumerate(lines):
            # Remove extra whitespace for compact display
            line = line.strip()
            
            # Skip empty lines
            if not line:
                y_pos += line_height
                continue
            
            # Determine line color based on content
            if re.match(r'^\s*#', line):  # Preprocessor directive
                fill_color = get_color("type")
            elif re.match(r'^\s*\/\/', line):  # Comment
                fill_color = get_color("comment")
            elif re.match(r'^\s*\/\*', line):  # Block comment start
                fill_color = get_color("comment")
            elif re.match(r'^.*\*\/\s*$', line):  # Block comment end
                fill_color = get_color("comment")
            elif re.search(r'(int|void|char|float|double|struct|enum)\s+\w+\s*\(', line):  # Function
                fill_color = get_color("function")
            elif "{" in line or "}" in line:  # Braces
                fill_color = get_color("operator")
            else:
                fill_color = get_color("fg_secondary")
            
            # Create simplified representation
            line_width = min(self.width - 4, len(line) * int(8 * self.scale_factor))
            self.create_rectangle(
                2, y_pos, 2 + line_width, y_pos + line_height - 1,
                fill=fill_color, outline=""
            )
            
            y_pos += line_height
        
        # Highlight visible area
        self._highlight_visible_area()
    
    def _highlight_visible_area(self):
        """Highlight the currently visible area in the editor"""
        # Get editor dimensions
        editor_height = self.editor.winfo_height()
        
        # Get first and last visible line
        try:
            first_visible = self.editor.index("@0,0").split('.')[0]
            last_visible = self.editor.index(f"@0,{editor_height}").split('.')[0]
            
            # Convert to integers
            first_line = int(first_visible)
            last_line = int(last_visible)
            
            # Calculate positions in minimap
            line_height = max(1, int(14 * self.scale_factor))
            first_y = (first_line - 1) * line_height
            last_y = (last_line) * line_height
            
            # Draw visible area highlight
            self.create_rectangle(
                0, first_y, self.width, last_y,
                fill="", outline=get_color("accent_primary"), width=2
            )
        except Exception as e:
            # Handle any exceptions during highlighting
            print(f"Error highlighting visible area: {e}")
    
    def on_minimap_click(self, event):
        """Handle click on the minimap to navigate to that position"""
        self._scroll_editor_to_position(event.y)
    
    def on_minimap_drag(self, event):
        """Handle drag on the minimap to scroll the editor"""
        self._scroll_editor_to_position(event.y)
    
    def _scroll_editor_to_position(self, y_position):
        """Scroll the editor to the position clicked in the minimap"""
        # Calculate which line was clicked
        line_height = max(1, int(14 * self.scale_factor))
        line_number = int(y_position / line_height) + 1
        
        # Get total lines
        content = self.editor.get("1.0", "end-1c")
        total_lines = content.count('\n') + 1
        
        # Ensure line number is valid
        line_number = max(1, min(line_number, total_lines))
        
        # Scroll editor to that line
        self.editor.see(f"{line_number}.0")
        
        # Update minimap highlight
        self.update_minimap()
    
    def update_theme(self):
        """Update minimap colors when theme changes"""
        self.configure(bg=get_color("bg_secondary"))
        self.update_minimap()
