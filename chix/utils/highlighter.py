"""
Syntax highlighter for C code using Pygments
"""

import customtkinter as ctk
import tkinter as tk
import re
import pygments
from pygments.lexers import CLexer
from pygments.token import Token
from chix.ui.theme import get_color

def highlight_syntax(editor):
    """
    Highlight syntax in the given editor widget using Pygments
    
    Args:
        editor: The EnhancedTextEditor widget
    """
    # Get the underlying Tkinter Text widget
    text_widget = editor._textbox
    
    # Get current content
    content = editor.get("1.0", "end-1c")
    
    # Save current cursor position
    current_pos = editor.index(tk.INSERT)
    
    # Clear existing highlighting tags
    for tag in text_widget.tag_names():
        if tag not in ["sel", "current_line", "matching_bracket"]:
            text_widget.tag_remove(tag, "1.0", "end")
    
    # Configure tags with theme colors
    text_widget.tag_configure("keyword", foreground=get_color("keyword"))
    text_widget.tag_configure("string", foreground=get_color("string"))
    text_widget.tag_configure("comment", foreground=get_color("comment"))
    text_widget.tag_configure("function", foreground=get_color("function"))
    text_widget.tag_configure("preprocessor", foreground=get_color("type"))
    text_widget.tag_configure("type", foreground=get_color("type"))
    text_widget.tag_configure("number", foreground=get_color("number"))
    text_widget.tag_configure("operator", foreground=get_color("operator"))
    text_widget.tag_configure("variable", foreground=get_color("variable"))
    text_widget.tag_configure("parameter", foreground=get_color("parameter"))
    
    try:
        # Apply syntax highlighting
        lexer = CLexer()
        tokens = lexer.get_tokens(content)
        
        pos = 0
        for token, text in tokens:
            start_index = "1.0 + %d chars" % pos
            end_index = "1.0 + %d chars" % (pos + len(text))
            
            if token in Token.Keyword:
                text_widget.tag_add("keyword", start_index, end_index)
            elif token in Token.String:
                text_widget.tag_add("string", start_index, end_index)
            elif token in Token.Comment:
                text_widget.tag_add("comment", start_index, end_index)
            elif token in Token.Name.Function:
                text_widget.tag_add("function", start_index, end_index)
            elif token in Token.Name.Builtin:
                text_widget.tag_add("type", start_index, end_index)
            elif token in Token.Literal.Number:
                text_widget.tag_add("number", start_index, end_index)
            elif token in Token.Operator:
                text_widget.tag_add("operator", start_index, end_index)
            elif token in Token.Name:
                # Check for specific names like variables vs parameters
                if pos > 0 and content[pos-1] == "(":
                    text_widget.tag_add("parameter", start_index, end_index)
                else:
                    text_widget.tag_add("variable", start_index, end_index)
            
            # Special case for preprocessor directives
            if text.startswith("#"):
                text_widget.tag_add("preprocessor", start_index, end_index)
                
            pos += len(text)
        
        # Highlight matching brackets
        highlight_matching_brackets(editor)
        
        # Check for syntax errors
        check_syntax_errors(editor)
        
    except Exception as e:
        print(f"Highlighting error: {e}")
    
    # Restore cursor position
    editor.mark_set(tk.INSERT, current_pos)
    editor.see(current_pos)

def highlight_matching_brackets(editor):
    """
    Highlight matching brackets/parentheses around cursor
    
    Args:
        editor: The EnhancedTextEditor widget
    """
    text_widget = editor._textbox
    content = editor.get("1.0", "end-1c")
    
    # Clear previous bracket matches
    text_widget.tag_remove("matching_bracket", "1.0", "end")
    
    # Get cursor position
    cursor_pos = editor.index(tk.INSERT)
    line, col = map(int, cursor_pos.split('.'))
    
    # Bracket pairs
    brackets = {')': '(', ']': '[', '}': '{', '(': ')', '[': ']', '{': '}'}
    
    # Check character before and at cursor
    try:
        char_before = editor.get(f"{line}.{col-1}", f"{line}.{col}")
        char_at = editor.get(f"{line}.{col}", f"{line}.{col+1}")
        
        # Process if either character is a bracket
        for char, pos in [(char_before, col-1), (char_at, col)]:
            if char in brackets:
                # Determine search direction and matching bracket
                if char in '({[':
                    # Forward search
                    stack = 0
                    for i in range(len(content)):
                        idx = text_widget.index(f"{line}.{pos}") + " + %d chars" % i
                        if text_widget.get(idx, idx + " + 1 chars") == char:
                            stack += 1
                        elif text_widget.get(idx, idx + " + 1 chars") == brackets[char]:
                            stack -= 1
                            if stack == 0:
                                # Found matching closing bracket
                                text_widget.tag_add("matching_bracket", f"{line}.{pos}", f"{line}.{pos+1}")
                                text_widget.tag_add("matching_bracket", idx, idx + " + 1 chars")
                                break
                else:
                    # Backward search
                    stack = 0
                    for i in range(len(content)):
                        idx = text_widget.index(f"{line}.{pos}") + " - %d chars" % i
                        if text_widget.get(idx, idx + " + 1 chars") == char:
                            stack += 1
                        elif text_widget.get(idx, idx + " + 1 chars") == brackets[char]:
                            stack -= 1
                            if stack == 0:
                                # Found matching opening bracket
                                text_widget.tag_add("matching_bracket", f"{line}.{pos}", f"{line}.{pos+1}")
                                text_widget.tag_add("matching_bracket", idx, idx + " + 1 chars")
                                break
    except Exception as e:
        # Handle any exceptions during bracket matching
        pass

def check_syntax_errors(editor):
    """
    Check for basic syntax errors in C code
    
    Args:
        editor: The EnhancedTextEditor widget
    """
    # Clear existing errors
    if hasattr(editor, "clear_errors"):
        editor.clear_errors()
    
    content = editor.get("1.0", "end-1c")
    lines = content.split('\n')
    
    # Basic error checks
    for i, line in enumerate(lines, 1):
        # Check for unclosed strings
        if re.search(r'\"[^\"]*$', line) and not line.strip().endswith("\\"):
            editor.mark_error(i, "Unclosed string literal")
        
        # Check for missing semicolons in statements (basic check)
        if (re.search(r'^\s*(int|char|float|double|void)\s+\w+\s*=.+', line) and 
            not line.strip().endswith(";") and 
            not line.strip().endswith("{")):
            editor.mark_error(i, "Statement missing semicolon")
        
        # Check for unbalanced braces in the line
        open_braces = line.count('{')
        close_braces = line.count('}')
        if open_braces != close_braces and ('{' in line or '}' in line):
            # Only mark as error if it's not a function or block definition
            if not re.search(r'^\s*\w+\s*\(.*\)\s*{', line):
                editor.mark_error(i, "Unbalanced braces")
