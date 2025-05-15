"""
Code runner for ChiX Editor
Handles running C code using either compiler or interpreter
"""

import os
import platform
import subprocess
import threading
import time
from chix.core.compiler import Compiler
from chix.core.interpreter import Interpreter

class Runner:
    """
    Handles running C code using either compiler or interpreter
    """
    
    def __init__(self, state):
        """
        Initialize the runner
        
        Args:
            state (dict): Application state
        """
        self.state = state
        self.compiler = Compiler()
        self.interpreter = Interpreter()
        self.current_process = None
        self.run_thread = None
        
        # Create temp directories if they don't exist
        os.makedirs("temp", exist_ok=True)
    
    def run_code(self, mode="compiler"):
        """
        Run the current code using either compiler or interpreter
        
        Args:
            mode (str): Mode to use - "compiler" or "interpreter"
        
        Returns:
            bool: True if successful, False otherwise
        """
        editor = self.state.get("active_editor")
        output = self.state.get("output")
        
        if not editor or not output:
            return False
        
        # Get code from editor
        code = editor.get("1.0", "end-1c")
        
        # Clear output
        output.delete("1.0", "end")
        
        # Get current file path or create a temporary file
        file_path = self.state.get("current_file")
        if not file_path:
            file_path = os.path.join("temp", "program.c")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
        
        # Choose run method based on mode
        if mode == "interpreter":
            return self._run_interpreter(code, file_path, output)
        else:
            return self._run_compiler(file_path, output)
    
    def _run_compiler(self, file_path, output):
        """
        Run code using the compiler
        
        Args:
            file_path (str): Path to the source file
            output (widget): Output widget for messages
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not file_path:
            output.insert("end", "[ERROR] No file to compile.\n")
            return False
        
        if not self.compiler.is_available():
            output.insert("end", "[ERROR] No C compiler detected.\n")
            output.insert("end", "Please install GCC, Clang, or TCC and make sure it's in your PATH.\n")
            return False
        
        # Show compiler info
        compiler_info = self.compiler.get_compiler_info()
        output.insert("end", f"[INFO] {compiler_info}\n")
        
        # Make sure file exists
        if not os.path.exists(file_path):
            output.insert("end", f"[ERROR] Source file not found: {file_path}\n")
            return False
        
        # Define a thread function to run compilation
        def compile_thread():
            # Start compilation
            output.insert("end", f"[INFO] Compiling {os.path.basename(file_path)}...\n")
            
            # Compile the code
            result, process = self.compiler.compile_and_run(file_path)
            
            # Store the process
            self.current_process = process
            
            # Display the result
            if result.success:
                output.insert("end", "[SUCCESS] Compilation completed. Running program...\n")
                
                # Show warnings if any
                if result.warnings:
                    output.insert("end", "\n[WARNINGS]\n")
                    for warning in result.warnings:
                        output.insert("end", f"{warning}\n")
            else:
                output.insert("end", "[ERROR] Compilation failed:\n")
                
                # Show errors if any
                if result.errors:
                    for error in result.errors:
                        output.insert("end", f"{error}\n")
                else:
                    output.insert("end", result.message + "\n")
            
            # Scroll to the end
            output.see("end")
        
        # Run compilation in a separate thread
        self.run_thread = threading.Thread(target=compile_thread)
        self.run_thread.daemon = True
        self.run_thread.start()
        
        return True
    
    def _run_interpreter(self, code, file_path, output):
        """
        Run code using the interpreter
        
        Args:
            code (str): C code to interpret
            file_path (str): Path to the source file (for reference)
            output (widget): Output widget for messages
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.interpreter.is_available():
            output.insert("end", "[ERROR] TCC (Tiny C Compiler) is not available.\n")
            output.insert("end", "Please install TCC for interpretation mode.\n")
            return False
        
        # Show interpreter info
        interpreter_info = self.interpreter.get_interpreter_info()
        output.insert("end", f"[INFO] {interpreter_info}\n")
        
        # Define a thread function to run interpretation
        def interpret_thread():
            # Start interpretation
            output.insert("end", f"[INFO] Interpreting {os.path.basename(file_path)}...\n")
            
            # Interpret the code
            result = self.interpreter.interpret_code(code)
            
            # Display the result
            if result.success:
                output.insert("end", "[SUCCESS] Program output:\n\n")
                output.insert("end", result.output)
            else:
                output.insert("end", "[ERROR] Interpretation failed:\n")
                
                # Show errors if any
                if result.errors:
                    for error in result.errors:
                        output.insert("end", f"{error}\n")
                else:
                    output.insert("end", result.output + "\n")
            
            # Scroll to the end
            output.see("end")
        
        # Run interpretation in a separate thread
        self.run_thread = threading.Thread(target=interpret_thread)
        self.run_thread.daemon = True
        self.run_thread.start()
        
        return True
    
    def run_interactive(self, file_path=None):
        """
        Run the code interactively in a new terminal window
        
        Args:
            file_path (str, optional): Path to the source file
        
        Returns:
            bool: True if successful, False otherwise
        """
        editor = self.state.get("active_editor")
        output = self.state.get("output")
        
        if not editor or not output:
            return False
        
        # Get current file path or use provided path
        if not file_path:
            file_path = self.state.get("current_file")
        
        if not file_path:
            output.insert("end", "[ERROR] Please save the file before running interactively.\n")
            return False
        
        # Determine whether to use compiler or interpreter
        mode = self.state.get("mode", "compiler")
        
        if mode == "interpreter":
            # Use interpreter in interactive mode
            if not self.interpreter.is_available():
                output.insert("end", "[ERROR] TCC (Tiny C Compiler) is not available.\n")
                return False
            
            success = self.interpreter.run_interactive(file_path)
            if success:
                output.insert("end", "[INFO] Running program interactively using TCC...\n")
                return True
            else:
                output.insert("end", "[ERROR] Failed to start interactive mode.\n")
                return False
        else:
            # Use compiler and run in a new terminal
            if not self.compiler.is_available():
                output.insert("end", "[ERROR] No C compiler detected.\n")
                return False
            
            # Compile the file
            result = self.compiler.compile(file_path)
            
            if result.success and result.executable_path:
                try:
                    # Run in a new terminal
                    if platform.system() == "Windows":
                        subprocess.Popen(f'start cmd /k "{result.executable_path}"', shell=True)
                    else:
                        # Try different terminal emulators
                        terminal_commands = [
                            ['x-terminal-emulator', '-e'],
                            ['gnome-terminal', '--'],
                            ['konsole', '-e'],
                            ['xterm', '-e']
                        ]
                        
                        for term_cmd in terminal_commands:
                            try:
                                subprocess.Popen(term_cmd + [result.executable_path])
                                break
                            except (subprocess.SubprocessError, FileNotFoundError):
                                continue
                        else:
                            # If no terminal works, use basic command
                            subprocess.Popen([result.executable_path])
                    
                    output.insert("end", "[INFO] Running program in a new terminal...\n")
                    return True
                except Exception as e:
                    output.insert("end", f"[ERROR] Failed to run in terminal: {str(e)}\n")
                    return False
            else:
                output.insert("end", "[ERROR] Compilation failed. Cannot run interactively.\n")
                return False
    
    def stop_execution(self):
        """
        Stop the currently running process
        
        Returns:
            bool: True if stopped, False if no process to stop
        """
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process = None
                return True
            except Exception:
                return False
        return False

# Global function to run code from the main application
def run_code(state, mode="compiler"):
    """
    Run code using the specified mode
    
    Args:
        state (dict): Application state
        mode (str): Mode to use - "compiler" or "interpreter"
    
    Returns:
        bool: True if successful, False otherwise
    """
    runner = Runner(state)
    return runner.run_code(mode)
