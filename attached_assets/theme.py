import customtkinter as ctk

def setup_theme():
    # Set appearance mode and theme
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Theme configuration for widgets - using the correct structure
    try:
        # Adjust button corner radius
        ctk.ThemeManager.theme["CTkButton"]["corner_radius"] = 4
        ctk.ThemeManager.theme["CTkButton"]["border_width"] = 0
        
        # Try to modify button colors if possible
        if "fg_color" in ctk.ThemeManager.theme["CTkButton"]:
            ctk.ThemeManager.theme["CTkButton"]["fg_color"] = ["#3e79cc", "#3e79cc"]
        if "hover_color" in ctk.ThemeManager.theme["CTkButton"]:
            ctk.ThemeManager.theme["CTkButton"]["hover_color"] = ["#5294e2", "#5294e2"]
    except (KeyError, AttributeError):
        # If we can't access theme directly, just skip custom styling
        pass