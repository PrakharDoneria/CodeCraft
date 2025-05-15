import customtkinter as ctk
import re
import pygments
from pygments.lexers import CLexer
from pygments.token import Token

def highlight(editor):
    """Syntax highlighting for C code using Pygments"""
    # Get the underlying Tkinter Text widget from CustomTkinter's CTkTextbox
    text_widget = editor._textbox
    
    content = editor.get("1.0", "end-1c")
    
    # Save current cursor position
    current_pos = editor.index(ctk.INSERT)
    
    # Clear all existing tags
    for tag in text_widget.tag_names():
        if tag != "sel":  # Don't remove selection
            text_widget.tag_remove(tag, "1.0", "end")
            
    # Configure tags for different token types
    text_widget.tag_configure("keyword", foreground="#569cd6")    # Blue
    text_widget.tag_configure("string", foreground="#ce9178")     # Orange/Brown
    text_widget.tag_configure("comment", foreground="#6A9955")    # Green
    text_widget.tag_configure("function", foreground="#dcdcaa")   # Yellow
    text_widget.tag_configure("preprocessor", foreground="#c586c0")  # Pink
    text_widget.tag_configure("type", foreground="#4ec9b0")       # Teal
    text_widget.tag_configure("number", foreground="#b5cea8")     # Light Green
    text_widget.tag_configure("operator", foreground="#d4d4d4")   # Light Gray
    text_widget.tag_configure("bracket", foreground="#d4d4d4")    # Light Gray
    
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
        elif token in Token.Punctuation:
            text_widget.tag_add("bracket", start_index, end_index)
        elif text.startswith("#"):
            text_widget.tag_add("preprocessor", start_index, end_index)
            
        pos += len(text)
    
    # Restore cursor position
    editor.mark_set(ctk.INSERT, current_pos)
    editor.see(current_pos)