"""
File operations for ChiX Editor
Handles file open, save, and related operations
"""

import os
import customtkinter as ctk
from tkinter import filedialog
import tkinter as tk
import shutil
import tempfile
import mimetypes
import time
import uuid

def new_file(state):
    """
    Create a new file and clear the editor
    
    Args:
        state (dict): Application state
    """
    if "main_panel" in state:
        state["main_panel"].create_new_tab()

def open_file(state, on_file_selected=None):
    """
    Open a file dialog and load selected file into the editor
    
    Args:
        state (dict): Application state
        on_file_selected (function): Callback when file is selected
    
    Returns:
        str: Path to the opened file or None if canceled
    """
    file_path = filedialog.askopenfilename(
        title="Open File",
        filetypes=[
            ("C Files", "*.c"),
            ("Header Files", "*.h"),
            ("All Files", "*.*")
        ],
        initialdir=state.get("current_directory", os.getcwd())
    )
    
    if file_path:
        # Update current directory
        state["current_directory"] = os.path.dirname(file_path)
        
        if callable(on_file_selected):
            on_file_selected(file_path)
        return file_path
    
    return None

def save_file(state, editor=None, file_path=None):
    """
    Save the current file
    
    Args:
        state (dict): Application state
        editor (widget, optional): Editor widget
        file_path (str, optional): Path to save to
    
    Returns:
        bool: True if saved successfully, False otherwise
    """
    # Use editor from arguments or get from state
    if not editor and "active_editor" in state:
        editor = state["active_editor"]
    
    # Use file_path from arguments or get from state
    if not file_path and "current_file" in state:
        file_path = state["current_file"]
    
    if not editor or not file_path:
        return save_file_as(state, editor)
    
    try:
        # Get content from editor
        content = editor.get("1.0", "end-1c")
        
        # Create backup file
        backup_path = _create_backup(file_path)
        
        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Update status message
        if "status_bar" in state:
            filename = os.path.basename(file_path)
            state["status_bar"].set_message(f"Saved {filename}")
        
        return True
    except Exception as e:
        # Update status message with error
        if "status_bar" in state:
            state["status_bar"].set_message(f"Error saving file: {str(e)}")
        
        # Restore from backup if it exists
        if 'backup_path' in locals():
            _restore_from_backup(backup_path, file_path)
        
        return False

def save_file_as(state, editor=None, file_path=None):
    """
    Save file with a new name
    
    Args:
        state (dict): Application state
        editor (widget, optional): Editor widget
        file_path (str, optional): Suggested file path
    
    Returns:
        str: New file path if saved, None otherwise
    """
    # Use editor from arguments or get from state
    if not editor and "active_editor" in state:
        editor = state["active_editor"]
    
    if not editor:
        return None
    
    # Get content from editor
    content = editor.get("1.0", "end-1c")
    
    # Initial directory
    initial_dir = state.get("current_directory", os.getcwd())
    if file_path:
        initial_dir = os.path.dirname(file_path)
    
    # Initial filename
    initial_file = ""
    if file_path:
        initial_file = os.path.basename(file_path)
    
    # Show save dialog
    new_path = filedialog.asksaveasfilename(
        title="Save As",
        defaultextension=".c",
        filetypes=[
            ("C Files", "*.c"),
            ("Header Files", "*.h"),
            ("All Files", "*.*")
        ],
        initialdir=initial_dir,
        initialfile=initial_file
    )
    
    if new_path:
        try:
            # Update current directory
            state["current_directory"] = os.path.dirname(new_path)
            
            # Write to file
            with open(new_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Update status message
            if "status_bar" in state:
                filename = os.path.basename(new_path)
                state["status_bar"].set_message(f"Saved as {filename}")
            
            # Return the new path
            return new_path
        except Exception as e:
            # Update status message with error
            if "status_bar" in state:
                state["status_bar"].set_message(f"Error saving file: {str(e)}")
    
    return None

def _create_backup(file_path):
    """
    Create a backup of a file
    
    Args:
        file_path (str): Path to the file to backup
    
    Returns:
        str: Path to the backup file or None if failed
    """
    try:
        if not os.path.exists(file_path):
            return None
        
        # Create backup filename
        backup_path = file_path + ".bak"
        
        # Copy original to backup
        shutil.copy2(file_path, backup_path)
        
        return backup_path
    except Exception:
        return None

def _restore_from_backup(backup_path, file_path):
    """
    Restore a file from its backup
    
    Args:
        backup_path (str): Path to the backup file
        file_path (str): Path to restore to
    
    Returns:
        bool: True if restored successfully, False otherwise
    """
    try:
        if not backup_path or not os.path.exists(backup_path):
            return False
        
        # Copy backup to original
        shutil.copy2(backup_path, file_path)
        
        # Remove backup
        os.unlink(backup_path)
        
        return True
    except Exception:
        return False

def open_folder(state):
    """
    Open a folder dialog and set it as the current project
    
    Args:
        state (dict): Application state
    
    Returns:
        str: Path to the opened folder or None if canceled
    """
    folder_path = filedialog.askdirectory(
        title="Open Folder",
        initialdir=state.get("current_directory", os.getcwd())
    )
    
    if folder_path:
        # Update current directory
        state["current_directory"] = folder_path
        
        # Open in project manager
        if "project_manager" in state:
            state["project_manager"].open_project(folder_path)
        
        # Update file explorer
        if "file_explorer" in state:
            state["file_explorer"].load_directory(folder_path)
        
        return folder_path
    
    return None

def detect_file_type(file_path):
    """
    Detect the type of a file
    
    Args:
        file_path (str): Path to the file
    
    Returns:
        str: File type description
    """
    # Get file extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    # Common extensions
    if ext == '.c':
        return "C Source File"
    elif ext == '.h':
        return "C Header File"
    elif ext == '.cpp' or ext == '.cc':
        return "C++ Source File"
    elif ext == '.hpp':
        return "C++ Header File"
    elif ext == '.txt':
        return "Text File"
    elif ext == '.md':
        return "Markdown File"
    elif ext == '.json':
        return "JSON File"
    elif ext == '.xml':
        return "XML File"
    elif ext == '.exe':
        return "Executable File"
    
    # Use mimetypes for other types
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type
    
    return "Unknown File Type"

def read_file(file_path):
    """
    Read a file and return its contents
    
    Args:
        file_path (str): Path to the file
    
    Returns:
        str: File contents or error message
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encodings
        try:
            with open(file_path, "r", encoding="latin-1") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def get_recent_files(max_count=10):
    """
    Get list of recently opened files
    
    Args:
        max_count (int): Maximum number of files to return
    
    Returns:
        list: List of recent file paths
    """
    try:
        recent_files = []
        
        # Try to read from recent files list
        if os.path.exists("recent_files.txt"):
            with open("recent_files.txt", "r") as f:
                recent_files = [line.strip() for line in f.readlines()]
                
                # Filter out files that no longer exist
                recent_files = [f for f in recent_files if os.path.exists(f)]
                
                # Limit to max_count
                recent_files = recent_files[:max_count]
        
        return recent_files
    except Exception:
        return []

def add_recent_file(file_path, max_count=10):
    """
    Add a file to the recently opened files list
    
    Args:
        file_path (str): Path to add
        max_count (int): Maximum number of files to keep
    """
    try:
        # Get existing recent files
        recent_files = get_recent_files()
        
        # Remove this file if it's already in the list
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # Add to the beginning
        recent_files.insert(0, file_path)
        
        # Limit to max_count
        recent_files = recent_files[:max_count]
        
        # Write back to file
        with open("recent_files.txt", "w") as f:
            for path in recent_files:
                f.write(f"{path}\n")
    except Exception:
        pass

def get_temp_dir():
    """
    Get the temporary directory for autosaves
    
    Returns:
        str: Path to temporary directory
    """
    temp_dir = os.path.join(tempfile.gettempdir(), "chix_editor")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def save_to_temp(content, file_id=None):
    """
    Save content to a temporary file
    
    Args:
        content (str): Content to save
        file_id (str, optional): ID for the temp file
    
    Returns:
        str: Path to the temporary file
    """
    if not file_id:
        file_id = str(uuid.uuid4())
    
    temp_dir = get_temp_dir()
    temp_file = os.path.join(temp_dir, f"{file_id}.temp")
    
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(content)
        return temp_file
    except Exception as e:
        print(f"Error saving temporary file: {e}")
        return None

def load_from_temp(file_id):
    """
    Load content from a temporary file
    
    Args:
        file_id (str): ID of the temp file
    
    Returns:
        str: Content of the temporary file
    """
    temp_dir = get_temp_dir()
    temp_file = os.path.join(temp_dir, f"{file_id}.temp")
    
    if not os.path.exists(temp_file):
        return None
    
    try:
        with open(temp_file, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error loading temporary file: {e}")
        return None

def clean_temp_files(max_age_hours=24):
    """
    Clean up old temporary files
    
    Args:
        max_age_hours (int): Maximum age in hours
    """
    temp_dir = get_temp_dir()
    
    if not os.path.exists(temp_dir):
        return
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 60 * 60
    
    try:
        for filename in os.listdir(temp_dir):
            if not filename.endswith(".temp"):
                continue
                
            file_path = os.path.join(temp_dir, filename)
            file_age = current_time - os.path.getmtime(file_path)
            
            if file_age > max_age_seconds:
                os.unlink(file_path)
    except Exception as e:
        print(f"Error cleaning temporary files: {e}")
