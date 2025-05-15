"""
Project management for ChiX Editor
Handles project loading, saving, and configuration
"""

import os
import json
import datetime
import shutil
from tkinter import filedialog, messagebox
import tkinter as tk

class ProjectManager:
    """
    Manages project-related functionality
    """
    
    def __init__(self, state):
        """
        Initialize the project manager
        
        Args:
            state (dict): Application state
        """
        self.state = state
        self.project_config = {}
        self.project_path = None
        
    def _create_project_config(self):
        """
        Create a new project configuration file
        """
        if not self.project_path:
            return
            
        # Create config directory if it doesn't exist
        config_dir = os.path.join(self.project_path, ".chix")
        os.makedirs(config_dir, exist_ok=True)
        
        # Create basic config
        self.project_config = {
            "name": os.path.basename(self.project_path),
            "created": datetime.datetime.now().isoformat(),
            "settings": {
                "theme_mode": self.state.get("theme_mode", "dark"),
                "tab_size": self.state.get("tab_size", 4),
                "word_wrap": self.state.get("word_wrap", False)
            },
            "recent_files": []
        }
        
        # Save to file
        config_path = os.path.join(config_dir, "project.json")
        try:
            with open(config_path, "w") as f:
                json.dump(self.project_config, f, indent=4)
        except Exception as e:
            print(f"Error saving project config: {e}")
            
    def save_editor_state(self):
        """
        Save the current editor state to the project configuration
        """
        if not self.project_path:
            return
            
        # Update config with current editor settings
        self.project_config["settings"] = {
            "theme_mode": self.state.get("theme_mode", "dark"),
            "tab_size": self.state.get("tab_size", 4),
            "word_wrap": self.state.get("word_wrap", False),
            "show_minimap": self.state.get("show_minimap", True)
        }
        
        # Get recent files from main panel
        if "main_panel" in self.state:
            recent_files = []
            for tab_id, tab_data in self.state["main_panel"].tab_view.tabs.items():
                if tab_data.get("file_path"):
                    # Store relative path if inside project
                    file_path = tab_data["file_path"]
                    if file_path.startswith(self.project_path):
                        file_path = os.path.relpath(file_path, self.project_path)
                    recent_files.append(file_path)
            
            if recent_files:
                self.project_config["recent_files"] = recent_files
        
        # Save to file
        config_path = os.path.join(self.project_path, ".chix", "project.json")
        try:
            with open(config_path, "w") as f:
                json.dump(self.project_config, f, indent=4)
        except Exception as e:
            print(f"Error saving project config: {e}")
    
    def open_project(self, project_path):
        """
        Open a project from a directory
        
        Args:
            project_path (str): Path to the project directory
        
        Returns:
            bool: True if project was opened successfully
        """
        if not os.path.isdir(project_path):
            return False
        
        # Update project path
        self.project_path = project_path
        self.state["current_directory"] = project_path
        self.state["current_project"] = project_path
        
        # Try to load project configuration
        config_path = os.path.join(project_path, ".chix", "project.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    self.project_config = json.load(f)
                
                # Update application state with project settings
                if "settings" in self.project_config:
                    for key, value in self.project_config["settings"].items():
                        self.state[key] = value
                
                # Update window title
                if "app" in self.state:
                    project_name = os.path.basename(project_path)
                    self.state["app"].title(f"ChiX - {project_name}")
                
                # Update status bar
                if "status_bar" in self.state:
                    self.state["status_bar"].set_message(f"Project opened: {os.path.basename(project_path)}")
                
                # Load recent files if any
                if "recent_files" in self.project_config and "main_panel" in self.state:
                    # Only load the most recent file
                    if self.project_config["recent_files"]:
                        recent_file = self.project_config["recent_files"][0]
                        full_path = os.path.join(project_path, recent_file)
                        if os.path.exists(full_path):
                            self.state["main_panel"].tab_view.open_file(full_path)
                
                return True
            except Exception as e:
                print(f"Error loading project configuration: {e}")
        
        # No configuration found, create default
        self._create_project_config()
        
        # Update window title
        if "app" in self.state:
            project_name = os.path.basename(project_path)
            self.state["app"].title(f"ChiX - {project_name}")
        
        # Update status bar
        if "status_bar" in self.state:
            self.state["status_bar"].set_message(f"Project opened: {os.path.basename(project_path)}")
        
        return True
    
    def create_project(self, project_path, template=None):
        """
        Create a new project
        
        Args:
            project_path (str): Path where to create the project
            template (str, optional): Project template to use
        
        Returns:
            bool: True if project was created successfully
        """
        if os.path.exists(project_path):
            # Check if directory is empty
            if os.listdir(project_path):
                return False
        else:
            try:
                os.makedirs(project_path)
            except Exception:
                return False
        
        # Create project structure
        try:
            # Create .chix directory for project metadata
            os.makedirs(os.path.join(project_path, ".chix"), exist_ok=True)
            
            # Create project configuration
            self.project_path = project_path
            self._create_project_config()
            
            # Create basic source structure
            os.makedirs(os.path.join(project_path, "src"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "include"), exist_ok=True)
            
            # Create a basic main.c file if no template is specified
            if not template:
                main_c_path = os.path.join(project_path, "src", "main.c")
                with open(main_c_path, "w") as f:
                    f.write("""/**
 * Main entry point for the application
 */
#include <stdio.h>

int main(int argc, char *argv[]) {
    printf("Hello, World!\\n");
    return 0;
}
""")
                
                # Create a basic Makefile
                makefile_path = os.path.join(project_path, "Makefile")
                with open(makefile_path, "w") as f:
                    f.write("""# Makefile for C project

CC = gcc
CFLAGS = -Wall -Wextra -g
INCLUDES = -Iinclude
SRC_DIR = src
OBJ_DIR = obj
BIN_DIR = bin

# Find all .c files in SRC_DIR
SRCS = $(wildcard $(SRC_DIR)/*.c)
# Generate .o file names corresponding to .c files
OBJS = $(patsubst $(SRC_DIR)/%.c, $(OBJ_DIR)/%.o, $(SRCS))
# Name of the final executable
TARGET = $(BIN_DIR)/program

# Default target
all: $(TARGET)

# Create directories if they don't exist
$(OBJ_DIR) $(BIN_DIR):
        mkdir -p $@

# Compile .c files to .o files
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c | $(OBJ_DIR)
        $(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

# Link .o files to create the executable
$(TARGET): $(OBJS) | $(BIN_DIR)
        $(CC) $(CFLAGS) $^ -o $@

# Run the program
run: $(TARGET)
        $(TARGET)

# Clean generated files
clean:
        rm -rf $(OBJ_DIR) $(BIN_DIR)

.PHONY: all run clean
""")
                
                # Create a README.md file
                readme_path = os.path.join(project_path, "README.md")
                with open(readme_path, "w") as f:
                    project_name = os.path.basename(project_path)
                    f.write(f"""# {project_name}

A C project created with ChiX Editor.

## Building

To build the project, run:

```
make
```

## Running

To run the project, use:

```
make run
```
""")
            
            return True
            
        except Exception as e:
            print(f"Error creating project: {str(e)}")
            return False
