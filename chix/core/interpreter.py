"""
C code interpreter for ChiX Editor
Uses TCC (Tiny C Compiler) to interpret C code without compilation
"""

import subprocess
import os
import platform
import tempfile
import time
import threading
import shutil

class InterpretationResult:
    """Stores the result of an interpretation operation"""
    
    def __init__(self, success, output, errors=None):
        """
        Initialize the interpretation result
        
        Args:
            success (bool): Whether interpretation was successful
            output (str): Program output or error message
            errors (list, optional): List of interpretation errors
        """
        self.success = success
        self.output = output
        self.errors = errors or []

class Interpreter:
    """Handles interpretation of C code using TCC"""
    
    def __init__(self):
        """Initialize the interpreter"""
        self.tcc_path = self._detect_tcc()
        self.temp_dir = os.path.join(tempfile.gettempdir(), "chix_interpreter")
        
        # Create temp directory if it doesn't exist
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir, exist_ok=True)
    
    def _detect_tcc(self):
        """
        Detect if TCC is available on the system
        
        Returns:
            str: Path to TCC or None if not found
        """
        try:
            # Try to run tcc to check if it's installed
            result = subprocess.run(
                ["tcc", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=1
            )
            
            if result.returncode == 0:
                return "tcc"
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        # On Windows, also look in common installation directories
        if platform.system() == "Windows":
            common_paths = [
                "C:\\tcc\\tcc.exe",
                "C:\\Program Files\\tcc\\tcc.exe",
                "C:\\Program Files (x86)\\tcc\\tcc.exe"
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    return path
        
        return None
    
    def is_available(self):
        """
        Check if TCC is available
        
        Returns:
            bool: True if TCC is available, False otherwise
        """
        return self.tcc_path is not None
    
    def get_interpreter_info(self):
        """
        Get information about the detected interpreter
        
        Returns:
            str: Interpreter information or error message
        """
        if not self.tcc_path:
            return "TCC (Tiny C Compiler) is not available. Please install TCC for interpretation mode."
        
        try:
            result = subprocess.run(
                [self.tcc_path, "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                return f"Using TCC (Tiny C Compiler) {result.stdout.strip()}"
            else:
                return "TCC is available but returned an error"
        except Exception as e:
            return f"Error getting interpreter info: {str(e)}"
    
    def interpret_file(self, source_path, args=None):
        """
        Interpret a C source file with TCC
        
        Args:
            source_path (str): Path to the C source file
            args (list, optional): Command-line arguments for the program
        
        Returns:
            InterpretationResult: Result of the interpretation
        """
        if not self.is_available():
            return InterpretationResult(
                False,
                "TCC (Tiny C Compiler) is not available. Please install TCC for interpretation mode.",
                ["Interpreter not found"]
            )
        
        if not os.path.exists(source_path):
            return InterpretationResult(
                False,
                f"Source file not found: {source_path}",
                ["Source file not found"]
            )
        
        try:
            # Build interpreter command
            cmd = [self.tcc_path, "-run", source_path]
            
            # Add program arguments if provided
            if args:
                cmd.extend(args)
            
            # Run the interpreter
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Set timeout for interpretation (10 seconds)
            start_time = time.time()
            stdout, stderr = '', ''
            
            # Process output
            while process.poll() is None:
                # Check for timeout
                if time.time() - start_time > 10:
                    process.terminate()
                    return InterpretationResult(
                        False,
                        "Interpretation timed out after 10 seconds",
                        ["Process timed out"]
                    )
                
                # Read output (non-blocking)
                stdout_line = process.stdout.readline()
                stderr_line = process.stderr.readline()
                
                if stdout_line:
                    stdout += stdout_line
                if stderr_line:
                    stderr += stderr_line
                
                # Sleep briefly to avoid high CPU usage
                time.sleep(0.1)
            
            # Get remaining output
            stdout_remaining, stderr_remaining = process.communicate()
            stdout += stdout_remaining
            stderr += stderr_remaining
            
            if process.returncode == 0:
                # Interpretation succeeded
                return InterpretationResult(
                    True,
                    stdout,
                    []
                )
            else:
                # Interpretation failed
                errors = stderr.strip().split('\n') if stderr.strip() else ["Unknown error"]
                return InterpretationResult(
                    False,
                    stderr,
                    errors
                )
            
        except Exception as e:
            return InterpretationResult(
                False,
                f"Interpretation error: {str(e)}",
                [str(e)]
            )
    
    def interpret_code(self, code, args=None):
        """
        Interpret C code directly (without saving to a file)
        
        Args:
            code (str): C code to interpret
            args (list, optional): Command-line arguments for the program
        
        Returns:
            InterpretationResult: Result of the interpretation
        """
        # Create temporary file
        temp_file = os.path.join(self.temp_dir, "temp_program.c")
        
        try:
            # Write code to temp file
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(code)
            
            # Interpret the file
            result = self.interpret_file(temp_file, args)
            
            # Clean up
            os.remove(temp_file)
            
            return result
            
        except Exception as e:
            # Clean up if possible
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            
            return InterpretationResult(
                False,
                f"Interpretation error: {str(e)}",
                [str(e)]
            )
    
    def run_interactive(self, source_path):
        """
        Run a C program interactively (in a new terminal window)
        
        Args:
            source_path (str): Path to the C source file
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if not self.is_available():
            return False
        
        if not os.path.exists(source_path):
            return False
        
        try:
            # Copy the source file to a temp location
            temp_file = os.path.join(self.temp_dir, "interactive_program.c")
            shutil.copy2(source_path, temp_file)
            
            # Run TCC in an interactive terminal
            if platform.system() == "Windows":
                # On Windows, open in a new command prompt
                cmd = f'start cmd /k "{self.tcc_path} -run {temp_file}"'
                subprocess.Popen(cmd, shell=True)
            else:
                # On Unix, try to open in a terminal
                terminal_commands = [
                    ['x-terminal-emulator', '-e'],
                    ['gnome-terminal', '--'],
                    ['konsole', '-e'],
                    ['xterm', '-e']
                ]
                
                # Try each terminal until one works
                for term_cmd in terminal_commands:
                    try:
                        subprocess.Popen(
                            term_cmd + [self.tcc_path, "-run", temp_file],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        break
                    except (subprocess.SubprocessError, FileNotFoundError):
                        continue
                else:
                    # If no terminal works, run directly
                    return False
            
            return True
            
        except Exception:
            return False
