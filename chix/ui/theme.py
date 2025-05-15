"""
Theme management for ChiX Editor
"""

import customtkinter as ctk
import json
import os

# Define color schemes
THEMES = {
    # VS Code Dark+ inspired theme
    "vscode_dark": {
        "bg_primary": "#1e1e1e",
        "bg_secondary": "#252526",
        "bg_tertiary": "#2d2d30",
        "bg_hover": "#3e3e42",
        "fg_primary": "#d4d4d4",
        "fg_secondary": "#9e9e9e",
        "accent_primary": "#007acc",
        "accent_secondary": "#3794ff",
        "error": "#f44747",
        "warning": "#ff8800",
        "success": "#35af74",
        "string": "#ce9178",
        "keyword": "#569cd6",
        "comment": "#6A9955",
        "function": "#dcdcaa",
        "type": "#4ec9b0",
        "number": "#b5cea8",
        "operator": "#d4d4d4",
        "variable": "#9cdcfe",
        "class": "#4ec9b0",
        "parameter": "#9cdcfe",
        "line_highlight": "#2a2d2e",
        "selection": "#264f78",
    },
    
    # Light theme
    "vscode_light": {
        "bg_primary": "#ffffff",
        "bg_secondary": "#f3f3f3",
        "bg_tertiary": "#e6e6e6",
        "bg_hover": "#d5d5d5",
        "fg_primary": "#333333",
        "fg_secondary": "#616161",
        "accent_primary": "#007acc",
        "accent_secondary": "#3794ff",
        "error": "#e51400",
        "warning": "#ff8c00",
        "success": "#008000",
        "string": "#a31515",
        "keyword": "#0000ff",
        "comment": "#008000",
        "function": "#795e26",
        "type": "#267f99",
        "number": "#098658",
        "operator": "#000000",
        "variable": "#001080",
        "class": "#267f99",
        "parameter": "#001080",
        "line_highlight": "#f8f8f8",
        "selection": "#add6ff",
    },
    
    # Dark theme with blue accents
    "dark_blue": {
        "bg_primary": "#1a1a1a",
        "bg_secondary": "#252525",
        "bg_tertiary": "#2d2d2d",
        "bg_hover": "#3e3e42",
        "fg_primary": "#d4d4d4",
        "fg_secondary": "#9e9e9e",
        "accent_primary": "#1e90ff",
        "accent_secondary": "#5b9bd5",
        "error": "#f44747",
        "warning": "#ff8800",
        "success": "#35af74",
        "string": "#ce9178",
        "keyword": "#569cd6",
        "comment": "#6A9955",
        "function": "#dcdcaa",
        "type": "#4ec9b0",
        "number": "#b5cea8",
        "operator": "#d4d4d4",
        "variable": "#9cdcfe",
        "class": "#4ec9b0",
        "parameter": "#9cdcfe",
        "line_highlight": "#2a2d2e",
        "selection": "#264f78",
    }
}

# Current theme - can be changed at runtime
current_theme = "vscode_dark"

def get_theme():
    """Get the current theme colors"""
    return THEMES[current_theme]

def get_color(color_key):
    """Get a specific color from the current theme"""
    theme = get_theme()
    return theme.get(color_key, "#ffffff")

def set_theme(theme_name):
    """Set the active theme"""
    global current_theme
    if theme_name in THEMES:
        current_theme = theme_name
        return True
    return False

def cycle_theme():
    """Cycle through available themes"""
    global current_theme
    theme_keys = list(THEMES.keys())
    current_index = theme_keys.index(current_theme)
    next_index = (current_index + 1) % len(theme_keys)
    current_theme = theme_keys[next_index]
    return current_theme

def setup_theme():
    """Set up the initial theme configuration"""
    # Set appearance mode 
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    try:
        # Customize button appearance
        ctk.ThemeManager.theme["CTkButton"]["corner_radius"] = 4
        ctk.ThemeManager.theme["CTkButton"]["border_width"] = 0
        
        # Apply theme colors
        theme = get_theme()
        
        # Apply to standard widgets
        ctk.ThemeManager.theme["CTkFrame"]["fg_color"] = [theme["bg_secondary"], theme["bg_secondary"]]
        ctk.ThemeManager.theme["CTkButton"]["fg_color"] = [theme["accent_primary"], theme["accent_primary"]]
        ctk.ThemeManager.theme["CTkButton"]["hover_color"] = [theme["accent_secondary"], theme["accent_secondary"]]
        ctk.ThemeManager.theme["CTkButton"]["text_color"] = [theme["fg_primary"], theme["fg_primary"]]
        
        # Apply to text-based widgets
        ctk.ThemeManager.theme["CTkTextbox"]["fg_color"] = [theme["bg_primary"], theme["bg_primary"]]
        ctk.ThemeManager.theme["CTkTextbox"]["text_color"] = [theme["fg_primary"], theme["fg_primary"]]
        
        # Apply to entry widgets
        ctk.ThemeManager.theme["CTkEntry"]["fg_color"] = [theme["bg_tertiary"], theme["bg_tertiary"]]
        ctk.ThemeManager.theme["CTkEntry"]["text_color"] = [theme["fg_primary"], theme["fg_primary"]]
        
    except (KeyError, AttributeError) as e:
        print(f"Warning: Error setting up theme: {e}")
        pass

def save_theme_preferences(file_path="theme_prefs.json"):
    """Save theme preferences to a file"""
    prefs = {
        "theme": current_theme,
    }
    
    try:
        with open(file_path, 'w') as f:
            json.dump(prefs, f)
    except Exception as e:
        print(f"Error saving theme preferences: {e}")

def load_theme_preferences(file_path="theme_prefs.json"):
    """Load theme preferences from a file"""
    global current_theme
    
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                prefs = json.load(f)
                if "theme" in prefs and prefs["theme"] in THEMES:
                    current_theme = prefs["theme"]
    except Exception as e:
        print(f"Error loading theme preferences: {e}")
