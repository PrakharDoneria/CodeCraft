"""
C compiler interface for ChiX Editor
Handles compilation of C code using external compilers
"""

import subprocess
import os
import platform
import re
import tempfile
import threading
import time

class CompilationResult:
    """Stores the result of a compilation operation"""
    
    def __init__(self, success, message, executable_path=None, warnings=None, errors=None):
        """
        Initialize the compilation result
        
        Args:
            success (bool): Whether compilation was successful
            message (str): Status message
            executable_path (str, optional): Path to the compiled executable
            warnings (list, optional): List of compilation warnings
            errors (list, optional): List of compilation errors
        """
        self.success = success
        self.message = message
        self.executable_path = executable_path
        self.warnings = warnings or []
        self.errors = errors or []

class Compiler:
    """Handles compilation of C code"""
    
    def __init__(self):
        """Initialize the compiler"""
        self.compiler_path = self._detect_compiler()
        self.temp_dir = os.path.join(tempfile.gettempdir(), "chix_compiler")
        
        # Create temp directory if it doesn't exist
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir, exist_ok=True)
    
    def _detect_compiler(self):
        """
        Detect available C compiler on the system
        
        Returns:
            str: Path to compiler or None if not found
        """
        compiler_commands = ["gcc", "clang", "tcc"]
        
        # On Windows, also check for MinGW
        if platform.system() == "Windows":
            compiler_commands.extend(["mingw32-gcc", "x86_64-w64-mingw32-gcc"])
        
        for compiler in compiler_commands:
            try:
                result = subprocess.run(
                    [compiler, "--version"], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    timeout=1
                )
                if result.returncode == 0:
                    return compiler
            except (subprocess.SubprocessError, FileNotFoundError):
                continue
        
        return None
    
    def is_available(self):
        """
        Check if a compiler is available
        
        Returns:
            bool: True if a compiler is available, False otherwise
        """
        return self.compiler_path is not None
    
    def get_compiler_info(self):
        """
        Get information about the detected compiler
        
        Returns:
            str: Compiler information or error message
        """
        if not self.compiler_path:
            return "No C compiler detected. Please install GCC, Clang, or TCC."
        
        try:
            result = subprocess.run(
                [self.compiler_path, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                # Extract first line of version info
                version_info = result.stdout.strip().split('\n')[0]
                return f"Using {version_info}"
            else:
                return f"Compiler error: {result.stderr.strip()}"
        except Exception as e:
            return f"Error getting compiler info: {str(e)}"
    
    def compile(self, source_path, output_path=None, options=None):
        """
        Compile a C source file
        
        Args:
            source_path (str): Path to the C source file
            output_path (str, optional): Path for the output executable
            options (list, optional): Additional compiler options
        
        Returns:
            CompilationResult: Result of the compilation
        """
        if not self.is_available():
            return CompilationResult(
                False, 
                "No C compiler detected. Please install GCC, Clang, or TCC.",
                None,
                [],
                ["Compiler not found"]
            )
        
        if not os.path.exists(source_path):
            return CompilationResult(
                False,
                f"Source file not found: {source_path}",
                None,
                [],
                ["Source file not found"]
            )
        
        # Create output path if not specified
        if not output_path:
            base_name = os.path.splitext(os.path.basename(source_path))[0]
            if platform.system() == "Windows":
                output_path = os.path.join(self.temp_dir, f"{base_name}.exe")
            else:
                output_path = os.path.join(self.temp_dir, base_name)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Remove previous executable if exists
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except Exception as e:
                return CompilationResult(
                    False,
                    f"Could not remove previous executable: {str(e)}",
                    None,
                    [],
                    [f"Failed to remove old executable: {str(e)}"]
                )
        
        # Build compiler command
        compiler_cmd = [self.compiler_path]
        
        # Add warning flags
        compiler_cmd.extend(['-Wall', '-Wextra', '-fdiagnostics-color=never'])
        
        # Add user options
        if options:
            compiler_cmd.extend(options)
        
        # Add source and output paths
        compiler_cmd.extend([source_path, '-o', output_path])
        
        try:
            # Run compiler
            process = subprocess.Popen(
                compiler_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Set timeout for compilation (10 seconds)
            start_time = time.time()
            stdout, stderr = '', ''
            
            # Process output
            while process.poll() is None:
                # Check for timeout
                if time.time() - start_time > 10:
                    process.terminate()
                    return CompilationResult(
                        False,
                        "Compilation timed out after 10 seconds",
                        None,
                        [],
                        ["Compilation process timed out"]
                    )
                
                # Read output
                stdout_data = process.stdout.readline()
                stderr_data = process.stderr.readline()
                
                if stdout_data:
                    stdout += stdout_data
                if stderr_data:
                    stderr += stderr_data
                
                # Sleep briefly to avoid high CPU usage
                time.sleep(0.1)
            
            # Get remaining output
            stdout_remaining, stderr_remaining = process.communicate()
            stdout += stdout_remaining
            stderr += stderr_remaining
            
            # Parse warnings and errors
            warnings, errors = self._parse_compiler_output(stderr)
            
            if process.returncode == 0:
                # Compilation succeeded
                return CompilationResult(
                    True,
                    "Compilation successful",
                    output_path,
                    warnings,
                    []
                )
            else:
                # Compilation failed
                return CompilationResult(
                    False,
                    "Compilation failed with errors",
                    None,
                    warnings,
                    errors
                )
            
        except Exception as e:
            return CompilationResult(
                False,
                f"Compilation process error: {str(e)}",
                None,
                [],
                [f"Process error: {str(e)}"]
            )
    
    def _parse_compiler_output(self, output):
        """
        Parse compiler output to extract warnings and errors
        
        Args:
            output (str): Compiler output text
        
        Returns:
            tuple: (warnings, errors) lists
        """
        warnings = []
        errors = []
        
        # Split output into lines
        lines = output.strip().split('\n')
        
        for line in lines:
            if not line.strip():
                continue
                
            # Look for warning/error indicators
            if 'warning:' in line.lower():
                warnings.append(line)
            elif 'error:' in line.lower():
                errors.append(line)
            elif 'note:' in line.lower():
                # Append notes to the last warning or error
                if errors:
                    errors[-1] += f"\n{line}"
                elif warnings:
                    warnings[-1] += f"\n{line}"
        
        return warnings, errors
    
    def compile_and_run(self, source_path, options=None):
        """
        Compile and run a C source file
        
        Args:
            source_path (str): Path to the C source file
            options (list, optional): Additional compiler options
        
        Returns:
            tuple: (CompilationResult, process) where process is the running process or None
        """
        # Compile the file
        result = self.compile(source_path, options=options)
        
        if result.success and result.executable_path:
            try:
                # Run the executable
                if platform.system() == "Windows":
                    # On Windows, open in a new command window
                    process = subprocess.Popen(
                        result.executable_path,
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
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
                            process = subprocess.Popen(
                                term_cmd + [result.executable_path],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                            )
                            break
                        except (subprocess.SubprocessError, FileNotFoundError):
                            continue
                    else:
                        # If no terminal works, run directly
                        process = subprocess.Popen(
                            [result.executable_path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                
                return result, process
            except Exception as e:
                result.success = False
                result.message = f"Failed to run executable: {str(e)}"
                return result, None
        
        return result, None
    
    def analyze_code(self, source_path):
        """
        Perform static analysis on C source code
        
        Args:
            source_path (str): Path to the C source file
        
        Returns:
            list: List of analysis findings
        """
        if not self.is_available():
            return [{"type": "error", "message": "No compiler available for analysis"}]
        
        if not os.path.exists(source_path):
            return [{"type": "error", "message": "Source file not found"}]
        
        findings = []
        
        try:
            # Run compiler with analysis flags
            cmd = [
                self.compiler_path,
                "-fsyntax-only",  # Don't generate code
                "-Wall",          # All warnings
                "-Wextra",        # Extra warnings
                "-Wpedantic",     # Pedantic warnings
                "-fdiagnostics-color=never",
                source_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            # Parse output for warnings/errors
            output = result.stderr.strip()
            
            for line in output.split('\n'):
                if not line.strip():
                    continue
                
                # Parse the line for file:line:col: message format
                match = re.search(r'(.*?):(\d+):(\d+):\s*(warning|error|note):\s*(.*)', line)
                if match:
                    file_path, line_num, col_num, msg_type, message = match.groups()
                    
                    findings.append({
                        "type": msg_type,
                        "file": file_path,
                        "line": int(line_num),
                        "column": int(col_num),
                        "message": message
                    })
                else:
                    # For lines that don't match the pattern, add them as-is
                    findings.append({
                        "type": "info",
                        "message": line
                    })
            
            return findings
            
        except Exception as e:
            return [{"type": "error", "message": f"Analysis error: {str(e)}"}]
