import customtkinter as ctk
from tkinter import filedialog
import os

def new_file(state):
    """Create a new file and clear the editor"""
    if state["editor"]:
        state["editor"].delete("1.0", "end")
        state["current_file"] = None
        
        # Update status bar if available
        if "status_bar" in state and state["status_bar"]:
            state["status_bar"].update_file_info()
        
        # Set window title
        if "app" in state and state["app"]:
            state["app"].title("ChiX - C Code Editor & Runner")

def open_file(state, highlight_func=None):
    """Open a file and load it into the editor"""
    file_path = filedialog.askopenfilename(
        filetypes=[
            ("C Files", "*.c"),
            ("Header Files", "*.h"),
            ("All Files", "*.*")
        ]
    )
    
    if file_path:
        try:
            with open(file_path, "r") as file:
                content = file.read()
                if state["editor"]:
                    state["editor"].delete("1.0", "end")
                    state["editor"].insert("1.0", content)
                    state["current_file"] = file_path
                    
                    # Apply syntax highlighting if function provided
                    if highlight_func:
                        highlight_func(state["editor"])
                    
                    # Update status bar if available
                    if "status_bar" in state and state["status_bar"]:
                        state["status_bar"].update_file_info(file_path)
                    
                    # Set window title
                    if "app" in state and state["app"]:
                        filename = os.path.basename(file_path)
                        state["app"].title(f"ChiX - {filename}")
                        
        except Exception as e:
            if state["output"]:
                state["output"].insert("end", f"Error opening file: {e}\n")

def save_file(state):
    """Save the current file"""
    if state["current_file"]:
        try:
            content = state["editor"].get("1.0", "end-1c")
            with open(state["current_file"], "w") as file:
                file.write(content)
                
            if state["output"]:
                state["output"].delete("1.0", "end")
                state["output"].insert("end", f"File saved: {state['current_file']}\n")
                
        except Exception as e:
            if state["output"]:
                state["output"].insert("end", f"Error saving file: {e}\n")
    else:
        save_file_as(state)

def save_file_as(state):
    """Save the current file as a new file"""
    file_path = filedialog.asksaveasfilename(
        defaultextension=".c",
        filetypes=[
            ("C Files", "*.c"),
            ("Header Files", "*.h"),
            ("All Files", "*.*")
        ]
    )
    
    if file_path:
        state["current_file"] = file_path
        save_file(state)
        
        # Update status bar if available
        if "status_bar" in state and state["status_bar"]:
            state["status_bar"].update_file_info(file_path)
        
        # Set window title
        if "app" in state and state["app"]:
            filename = os.path.basename(file_path)
            state["app"].title(f"ChiX - {filename}")