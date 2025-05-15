"""
C code formatter for ChiX Editor
Formats C code for better readability
"""

import re
import subprocess
import tempfile
import os

def format_c_code(code):
    """
    Format C code for better readability
    
    Args:
        code (str): Unformatted C code
    
    Returns:
        str: Formatted C code or original code if formatting fails
    """
    # Try to use external formatters first
    formatted = _try_external_formatters(code)
    if formatted:
        return formatted
    
    # Fall back to simple internal formatter
    return _simple_format(code)

def _try_external_formatters(code):
    """
    Try to format C code using external tools (clang-format, astyle, indent)
    
    Args:
        code (str): Unformatted C code
    
    Returns:
        str: Formatted code or None if failed
    """
    # Try clang-format first
    formatted = _try_clang_format(code)
    if formatted:
        return formatted
    
    # Try astyle
    formatted = _try_astyle(code)
    if formatted:
        return formatted
    
    # Try indent
    formatted = _try_indent(code)
    if formatted:
        return formatted
    
    # No formatters available
    return None

def _try_clang_format(code):
    """
    Try to format C code using clang-format
    
    Args:
        code (str): Unformatted C code
    
    Returns:
        str: Formatted code or None if clang-format isn't available
    """
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".c", delete=False) as temp_file:
            temp_file.write(code.encode('utf-8'))
            temp_file_path = temp_file.name
        
        # Run clang-format with Google style
        result = subprocess.run(
            ['clang-format', '-style=Google', temp_file_path],
            capture_output=True,
            text=True,
            timeout=5  # Timeout in seconds
        )
        
        # Cleanup temp file
        os.unlink(temp_file_path)
        
        # Check if successful
        if result.returncode == 0:
            return result.stdout
        
        return None
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        # Clean up if error occurred
        try:
            if 'temp_file_path' in locals():
                os.unlink(temp_file_path)
        except:
            pass
        return None

def _try_astyle(code):
    """
    Try to format C code using astyle
    
    Args:
        code (str): Unformatted C code
    
    Returns:
        str: Formatted code or None if astyle isn't available
    """
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".c", delete=False) as temp_file:
            temp_file.write(code.encode('utf-8'))
            temp_file_path = temp_file.name
        
        # Run astyle
        result = subprocess.run(
            ['astyle', '--style=google', temp_file_path],
            capture_output=True,
            text=True,
            timeout=5  # Timeout in seconds
        )
        
        # Read the formatted file
        with open(temp_file_path, 'r') as f:
            formatted_code = f.read()
        
        # Cleanup temp file
        os.unlink(temp_file_path)
        
        # Check if successful
        if result.returncode == 0:
            return formatted_code
        
        return None
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        # Clean up if error occurred
        try:
            if 'temp_file_path' in locals():
                os.unlink(temp_file_path)
        except:
            pass
        return None

def _try_indent(code):
    """
    Try to format C code using GNU indent
    
    Args:
        code (str): Unformatted C code
    
    Returns:
        str: Formatted code or None if indent isn't available
    """
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".c", delete=False) as temp_file:
            temp_file.write(code.encode('utf-8'))
            temp_file_path = temp_file.name
        
        # Run indent
        result = subprocess.run(
            ['indent', temp_file_path],
            capture_output=True,
            text=True,
            timeout=5  # Timeout in seconds
        )
        
        # Read the formatted file
        with open(temp_file_path, 'r') as f:
            formatted_code = f.read()
        
        # Cleanup temp file
        os.unlink(temp_file_path)
        
        # Check if successful
        if result.returncode == 0:
            return formatted_code
        
        return None
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        # Clean up if error occurred
        try:
            if 'temp_file_path' in locals():
                os.unlink(temp_file_path)
        except:
            pass
        return None

def _simple_format(code):
    """
    Simple internal C code formatter
    
    Args:
        code (str): Unformatted C code
    
    Returns:
        str: Formatted code
    """
    # Preserve empty newlines
    lines = code.split('\n')
    formatted_lines = []
    
    indent_level = 0
    indent_size = 4
    in_comment_block = False
    
    for line in lines:
        # Handle block comments
        if "/*" in line and "*/" not in line:
            in_comment_block = True
            formatted_lines.append(line)
            continue
        elif "*/" in line and in_comment_block:
            in_comment_block = False
            formatted_lines.append(line)
            continue
        elif in_comment_block:
            formatted_lines.append(line)
            continue
        
        # Skip empty lines
        if not line.strip():
            formatted_lines.append("")
            continue
        
        # Determine if we're closing a block
        closing_brace = line.strip() == "}" or line.strip().startswith("} ")
        if closing_brace and indent_level > 0:
            indent_level -= 1
        
        # Format the line with correct indentation
        indented_line = " " * (indent_level * indent_size) + line.strip()
        formatted_lines.append(indented_line)
        
        # Adjust indent level for next line based on braces
        open_braces = line.count("{")
        close_braces = line.count("}")
        
        # Only adjust indent on standalone braces 
        # (e.g., "if (condition) {" should increase indent)
        if open_braces > close_braces:
            indent_level += (open_braces - close_braces)
        
        # Add empty lines after certain statements
        if line.strip().endswith(";") and (
            line.strip().startswith("int ") or 
            line.strip().startswith("char ") or
            line.strip().startswith("float ") or
            line.strip().startswith("double ")
        ):
            # Add empty line after variable declarations
            if (len(formatted_lines) < 2 or not 
                (formatted_lines[-2].strip().endswith(";") and
                 any(formatted_lines[-2].strip().startswith(t) for t in 
                     ["int ", "char ", "float ", "double "]))
            ):
                formatted_lines.append("")
        
        # Add empty lines after closing braces for readability
        if closing_brace and not line.strip().endswith(";"):
            formatted_lines.append("")
    
    # Join lines and return
    return '\n'.join(formatted_lines)

def format_selection(code, start_line, end_line):
    """
    Format only a selected portion of code
    
    Args:
        code (str): Full code
        start_line (int): Starting line number (1-based)
        end_line (int): Ending line number (1-based)
    
    Returns:
        str: Code with formatted selection
    """
    lines = code.split('\n')
    
    # Extract the selection
    selection = '\n'.join(lines[start_line-1:end_line])
    
    # Format the selection
    formatted_selection = format_c_code(selection)
    
    # Replace the selection in the original code
    result = lines[:start_line-1] + formatted_selection.split('\n') + lines[end_line:]
    
    return '\n'.join(result)
