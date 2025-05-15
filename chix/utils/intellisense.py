"""
Code intelligence and autocompletion for C code
Provides code suggestions, function parameter info, etc.
"""

import re
import os
import tkinter as tk
from chix.ui.theme import get_color

# C language keywords
C_KEYWORDS = [
    "auto", "break", "case", "char", "const", "continue", "default", "do", "double",
    "else", "enum", "extern", "float", "for", "goto", "if", "int", "long", "register",
    "return", "short", "signed", "sizeof", "static", "struct", "switch", "typedef",
    "union", "unsigned", "void", "volatile", "while"
]

# C standard library functions with signatures
C_STD_FUNCTIONS = {
    "printf": {"signature": "int printf(const char *format, ...)", "desc": "Print formatted output to stdout"},
    "scanf": {"signature": "int scanf(const char *format, ...)", "desc": "Read formatted input from stdin"},
    "fprintf": {"signature": "int fprintf(FILE *stream, const char *format, ...)", "desc": "Print formatted output to a file"},
    "fscanf": {"signature": "int fscanf(FILE *stream, const char *format, ...)", "desc": "Read formatted input from a file"},
    "sprintf": {"signature": "int sprintf(char *str, const char *format, ...)", "desc": "Print formatted output to a string"},
    "sscanf": {"signature": "int sscanf(const char *str, const char *format, ...)", "desc": "Read formatted input from a string"},
    "fopen": {"signature": "FILE *fopen(const char *filename, const char *mode)", "desc": "Open a file"},
    "fclose": {"signature": "int fclose(FILE *stream)", "desc": "Close a file"},
    "fread": {"signature": "size_t fread(void *ptr, size_t size, size_t count, FILE *stream)", "desc": "Read from a file"},
    "fwrite": {"signature": "size_t fwrite(const void *ptr, size_t size, size_t count, FILE *stream)", "desc": "Write to a file"},
    "malloc": {"signature": "void *malloc(size_t size)", "desc": "Allocate memory"},
    "calloc": {"signature": "void *calloc(size_t nmemb, size_t size)", "desc": "Allocate and zero-initialize memory"},
    "realloc": {"signature": "void *realloc(void *ptr, size_t size)", "desc": "Reallocate memory"},
    "free": {"signature": "void free(void *ptr)", "desc": "Free allocated memory"},
    "memcpy": {"signature": "void *memcpy(void *dest, const void *src, size_t n)", "desc": "Copy memory area"},
    "memmove": {"signature": "void *memmove(void *dest, const void *src, size_t n)", "desc": "Copy memory area with overlapping support"},
    "memset": {"signature": "void *memset(void *s, int c, size_t n)", "desc": "Fill memory with a constant byte"},
    "strlen": {"signature": "size_t strlen(const char *s)", "desc": "Calculate the length of a string"},
    "strcpy": {"signature": "char *strcpy(char *dest, const char *src)", "desc": "Copy a string"},
    "strncpy": {"signature": "char *strncpy(char *dest, const char *src, size_t n)", "desc": "Copy a string with length limit"},
    "strcat": {"signature": "char *strcat(char *dest, const char *src)", "desc": "Concatenate strings"},
    "strncat": {"signature": "char *strncat(char *dest, const char *src, size_t n)", "desc": "Concatenate strings with length limit"},
    "strcmp": {"signature": "int strcmp(const char *s1, const char *s2)", "desc": "Compare strings"},
    "strncmp": {"signature": "int strncmp(const char *s1, const char *s2, size_t n)", "desc": "Compare strings with length limit"},
    "main": {"signature": "int main(int argc, char *argv[])", "desc": "Program entry point"}
}

# C preprocessor directives
C_PREPROCESSOR = [
    "#include", "#define", "#undef", "#ifdef", "#ifndef", "#if", "#else", "#elif", 
    "#endif", "#error", "#pragma"
]

# Common C snippets
C_SNIPPETS = {
    "main": "int main(int argc, char *argv[]) {\n    \n    return 0;\n}",
    "for": "for (int i = 0; i < n; i++) {\n    \n}",
    "while": "while (condition) {\n    \n}",
    "if": "if (condition) {\n    \n}",
    "else": "else {\n    \n}",
    "ifelse": "if (condition) {\n    \n} else {\n    \n}",
    "switch": "switch (expression) {\n    case constant1:\n        // code\n        break;\n    case constant2:\n        // code\n        break;\n    default:\n        // code\n        break;\n}",
    "struct": "struct name {\n    type member1;\n    type member2;\n};",
    "function": "return_type function_name(parameter_type parameter) {\n    \n    return value;\n}",
    "printf": "printf(\"%d\\n\", variable);",
    "scanf": "scanf(\"%d\", &variable);",
    "fopen": "FILE *file = fopen(\"filename\", \"mode\");\nif (file == NULL) {\n    // Handle error\n}",
    "malloc": "type *ptr = (type *)malloc(size * sizeof(type));\nif (ptr == NULL) {\n    // Handle error\n}",
    "include": "#include <stdio.h>\n#include <stdlib.h>",
}

class Intellisense:
    """
    Provides code intelligence features for the editor
    """
    
    def __init__(self, editor, state):
        """
        Initialize the intellisense engine
        
        Args:
            editor: The EnhancedTextEditor widget
            state: Application state
        """
        self.editor = editor
        self.state = state
        self.suggestion_window = None
        self.param_info_window = None
        
        # Project-specific symbols
        self.project_symbols = {
            "variables": {},  # name -> type
            "functions": {},  # name -> {return_type, params, desc}
            "structs": {},    # name -> {members}
            "enums": {},      # name -> {values}
            "typedefs": {},   # alias -> original
        }
        
        # Set up event bindings
        self._setup_events()
    
    def _setup_events(self):
        """Set up event bindings for intellisense"""
        # Trigger suggestions on relevant key presses
        self.editor.bind("<period>", self._trigger_member_suggestions)  # After a dot
        self.editor.bind("<greater>", self._trigger_member_suggestions)  # After -> (needs to check prev char)
        self.editor.bind("<space>", self._trigger_suggestions)  # After space or keywords
        self.editor.bind("<Return>", self._on_enter)
        self.editor.bind("<Tab>", self._try_complete_suggestion)
        
        # Dismiss suggestions on certain keys
        self.editor.bind("<Escape>", self._dismiss_suggestions)
        self.editor.bind("<FocusOut>", self._dismiss_suggestions)
        
        # Show parameter info when typing inside function call
        self.editor.bind("<parenleft>", self._show_param_info)  # After opening parenthesis
        self.editor.bind("<comma>", self._update_param_info)  # After comma inside function call
        
        # Update for cursor movement
        self.editor.bind("<KeyRelease>", self._on_key_release)
    
    def _on_key_release(self, event):
        """Handle key release events"""
        if event.keysym in ('Left', 'Right', 'Up', 'Down'):
            # Update suggestion window and parameter info if needed
            if self.suggestion_window:
                self._update_suggestions()
            if self.param_info_window:
                self._update_param_info()
    
    def _on_enter(self, event):
        """Handle enter key press"""
        # Dismiss suggestions
        self._dismiss_suggestions(event)
        return None  # Allow default handling
    
    def _trigger_suggestions(self, event=None):
        """Trigger code suggestions"""
        # Get current line and position
        cursor_pos = self.editor.index(tk.INSERT)
        line, col = map(int, cursor_pos.split('.'))
        
        # Get text up to cursor on current line
        line_text = self.editor.get(f"{line}.0", f"{line}.{col}")
        
        # Check for special cases
        if line_text.strip().startswith('#'):
            # After preprocessor directive
            self._show_preprocessor_suggestions(line_text)
        elif re.search(r'^\s*(int|char|float|double|void|struct|enum)\s+$', line_text):
            # After type declaration
            self._show_variable_suggestions(line_text)
        elif re.search(r'#include\s+[<"]', line_text):
            # After #include directive
            self._show_header_suggestions(line_text)
        else:
            # General suggestions
            word = self._get_current_word(line_text)
            self._show_general_suggestions(word)
        
        return None  # Allow default handling
    
    def _trigger_member_suggestions(self, event=None):
        """Trigger struct/pointer member suggestions"""
        # Check if it's really a member access
        cursor_pos = self.editor.index(tk.INSERT)
        line, col = map(int, cursor_pos.split('.'))
        
        # For -> operator, check if previous char was -
        if event and event.char == '>':
            prev_char = self.editor.get(f"{line}.{col-1}", f"{line}.{col}")
            if prev_char != '-':
                return None  # Not -> operator
        
        # Get the struct/pointer variable
        line_text = self.editor.get(f"{line}.0", f"{line}.{col}")
        
        # Extract variable name before . or ->
        if '.' in line_text:
            var_name = line_text.split('.')[-2].strip()
            self._show_member_suggestions(var_name)
        elif '->' in line_text:
            var_name = line_text.split('->')[-2].strip()
            self._show_member_suggestions(var_name, is_pointer=True)
        
        return None  # Allow default handling
    
    def _show_general_suggestions(self, prefix=""):
        """Show general code suggestions"""
        suggestions = []
        
        # Add keywords if they match prefix
        for keyword in C_KEYWORDS:
            if keyword.startswith(prefix):
                suggestions.append({
                    "text": keyword,
                    "type": "keyword",
                    "desc": "C keyword"
                })
        
        # Add standard functions
        for func, details in C_STD_FUNCTIONS.items():
            if func.startswith(prefix):
                suggestions.append({
                    "text": func,
                    "type": "function",
                    "desc": details["desc"],
                    "signature": details["signature"]
                })
        
        # Add project symbols
        # Variables
        for var, var_type in self.project_symbols["variables"].items():
            if var.startswith(prefix):
                suggestions.append({
                    "text": var,
                    "type": "variable",
                    "desc": f"Variable of type {var_type}"
                })
        
        # Functions
        for func, details in self.project_symbols["functions"].items():
            if func.startswith(prefix):
                params = ", ".join([f"{p['type']} {p['name']}" for p in details.get("params", [])])
                signature = f"{details.get('return_type', 'void')} {func}({params})"
                suggestions.append({
                    "text": func,
                    "type": "function",
                    "desc": details.get("desc", "User-defined function"),
                    "signature": signature
                })
        
        # Structs, enums, typedefs
        for struct_name in self.project_symbols["structs"]:
            if struct_name.startswith(prefix):
                suggestions.append({
                    "text": struct_name,
                    "type": "struct",
                    "desc": "User-defined struct"
                })
        
        for enum_name in self.project_symbols["enums"]:
            if enum_name.startswith(prefix):
                suggestions.append({
                    "text": enum_name,
                    "type": "enum",
                    "desc": "User-defined enum"
                })
        
        for typedef, original in self.project_symbols["typedefs"].items():
            if typedef.startswith(prefix):
                suggestions.append({
                    "text": typedef,
                    "type": "typedef",
                    "desc": f"Type alias for {original}"
                })
        
        # Add snippets
        for snippet_name, snippet_code in C_SNIPPETS.items():
            if snippet_name.startswith(prefix):
                suggestions.append({
                    "text": snippet_name,
                    "type": "snippet",
                    "desc": f"Snippet: {snippet_name}",
                    "code": snippet_code
                })
        
        # Show suggestions window if we have any
        if suggestions:
            self._show_suggestions_window(suggestions)
        else:
            self._dismiss_suggestions()
    
    def _show_preprocessor_suggestions(self, text):
        """Show preprocessor directive suggestions"""
        # Extract current directive
        match = re.search(r'#(\w*)$', text)
        if match:
            prefix = match.group(1)
            suggestions = []
            
            for directive in C_PREPROCESSOR:
                if directive[1:].startswith(prefix):
                    suggestions.append({
                        "text": directive,
                        "type": "preprocessor",
                        "desc": f"Preprocessor directive: {directive}"
                    })
            
            if suggestions:
                self._show_suggestions_window(suggestions)
    
    def _show_variable_suggestions(self, text):
        """Show suggestions after type declarations"""
        # Type declaration followed by incomplete variable name
        match = re.search(r'^\s*(int|char|float|double|void|struct|enum)\s+(\w*)$', text)
        if match:
            type_name = match.group(1)
            prefix = match.group(2)
            
            # Suggest variables of similar types from current file or project
            suggestions = []
            
            for var, var_type in self.project_symbols["variables"].items():
                if var_type == type_name and var.startswith(prefix):
                    suggestions.append({
                        "text": var,
                        "type": "variable",
                        "desc": f"Existing variable of type {var_type}"
                    })
            
            # If it's struct or enum, suggest known ones
            if type_name == "struct":
                for struct_name in self.project_symbols["structs"]:
                    if struct_name.startswith(prefix):
                        suggestions.append({
                            "text": struct_name,
                            "type": "struct",
                            "desc": "User-defined struct"
                        })
            elif type_name == "enum":
                for enum_name in self.project_symbols["enums"]:
                    if enum_name.startswith(prefix):
                        suggestions.append({
                            "text": enum_name,
                            "type": "enum",
                            "desc": "User-defined enum"
                        })
            
            if suggestions:
                self._show_suggestions_window(suggestions)
    
    def _show_header_suggestions(self, text):
        """Show suggestions for header files in #include statements"""
        # Extract partial header name
        if '<' in text:
            match = re.search(r'#include\s+<([^>]*)$', text)
            if match:
                prefix = match.group(1)
                self._show_standard_headers(prefix)
        elif '"' in text:
            match = re.search(r'#include\s+"([^"]*)$', text)
            if match:
                prefix = match.group(1)
                self._show_project_headers(prefix)
    
    def _show_standard_headers(self, prefix=""):
        """Show suggestions for standard C headers"""
        # List of common C standard headers
        std_headers = [
            "stdio.h", "stdlib.h", "string.h", "math.h", "ctype.h", "time.h",
            "stdarg.h", "stddef.h", "errno.h", "float.h", "limits.h", "assert.h",
            "signal.h", "setjmp.h", "locale.h", "iso646.h", "stdbool.h"
        ]
        
        suggestions = []
        for header in std_headers:
            if header.startswith(prefix):
                suggestions.append({
                    "text": header,
                    "type": "header",
                    "desc": f"Standard header file: {header}"
                })
        
        if suggestions:
            self._show_suggestions_window(suggestions)
    
    def _show_project_headers(self, prefix=""):
        """Show suggestions for project header files"""
        suggestions = []
        
        # Try to find project headers in the current directory and project
        if "current_directory" in self.state:
            dir_path = self.state["current_directory"]
            
            try:
                for filename in os.listdir(dir_path):
                    if filename.endswith('.h') and filename.startswith(prefix):
                        suggestions.append({
                            "text": filename,
                            "type": "header",
                            "desc": f"Project header file: {filename}"
                        })
            except Exception:
                pass
        
        if suggestions:
            self._show_suggestions_window(suggestions)
    
    def _show_member_suggestions(self, struct_var, is_pointer=False):
        """Show suggestions for struct or pointer members"""
        # Find the struct type of the variable
        var_type = self.project_symbols["variables"].get(struct_var, "")
        
        # Handle pointer syntax (e.g., struct name* -> struct name)
        if is_pointer and var_type.endswith('*'):
            var_type = var_type[:-1].strip()
        
        # If it's a struct, show its members
        if var_type.startswith("struct "):
            struct_name = var_type[7:].strip()
            struct_info = self.project_symbols["structs"].get(struct_name, {})
            
            suggestions = []
            for member, member_type in struct_info.get("members", {}).items():
                suggestions.append({
                    "text": member,
                    "type": "member",
                    "desc": f"{member_type} member of {struct_name}"
                })
            
            if suggestions:
                self._show_suggestions_window(suggestions)
    
    def _show_param_info(self, event=None):
        """Show parameter information for a function"""
        # Get current line and position
        cursor_pos = self.editor.index(tk.INSERT)
        line, col = map(int, cursor_pos.split('.'))
        
        # Get text up to cursor on current line
        line_text = self.editor.get(f"{line}.0", f"{line}.{col}")
        
        # Find the function name before the opening parenthesis
        match = re.search(r'(\w+)\s*\($', line_text)
        if match:
            func_name = match.group(1)
            
            # Check if it's a standard function
            if func_name in C_STD_FUNCTIONS:
                func_info = C_STD_FUNCTIONS[func_name]
                self._show_param_info_window(func_name, func_info["signature"], func_info["desc"])
            
            # Or a user-defined function
            elif func_name in self.project_symbols["functions"]:
                func_info = self.project_symbols["functions"][func_name]
                params = ", ".join([f"{p['type']} {p['name']}" for p in func_info.get("params", [])])
                signature = f"{func_info.get('return_type', 'void')} {func_name}({params})"
                self._show_param_info_window(func_name, signature, func_info.get("desc", ""))
        
        return None  # Allow default handling
    
    def _update_param_info(self, event=None):
        """Update parameter information when adding more arguments"""
        if self.param_info_window:
            # Get current line text up to cursor
            cursor_pos = self.editor.index(tk.INSERT)
            line, col = map(int, cursor_pos.split('.'))
            line_text = self.editor.get(f"{line}.0", f"{line}.{col}")
            
            # Count commas to determine which parameter to highlight
            open_paren_pos = line_text.rfind('(')
            if open_paren_pos >= 0:
                arg_text = line_text[open_paren_pos:]
                param_index = arg_text.count(',')
                
                # Update the parameter info window highlighting
                self._highlight_current_param(param_index)
        
        return None  # Allow default handling
    
    def _show_suggestions_window(self, suggestions):
        """Display the suggestions window"""
        # Close existing window
        if self.suggestion_window:
            self.suggestion_window.destroy()
        
        # Get cursor position on screen
        cursor_pos = self.editor.index(tk.INSERT)
        line, col = map(int, cursor_pos.split('.'))
        x, y, width, height = self.editor._textbox.bbox(cursor_pos)
        
        # Convert to screen coordinates
        x_screen = self.editor.winfo_rootx() + x
        y_screen = self.editor.winfo_rooty() + y + height
        
        # Create suggestion window
        self.suggestion_window = tk.Toplevel(self.editor)
        self.suggestion_window.wm_overrideredirect(True)  # No window decorations
        self.suggestion_window.wm_geometry(f"+{x_screen}+{y_screen}")
        
        # Configure window appearance
        self.suggestion_window.configure(bg=get_color("bg_secondary"))
        self.suggestion_window.bind("<FocusOut>", self._dismiss_suggestions)
        
        # Create listbox for suggestions
        listbox = tk.Listbox(
            self.suggestion_window,
            height=min(10, len(suggestions)),
            width=50,
            bg=get_color("bg_secondary"),
            fg=get_color("fg_primary"),
            selectbackground=get_color("selection"),
            selectforeground=get_color("fg_primary"),
            font=("Cascadia Code", 11),
            bd=1
        )
        
        # Fill listbox with suggestions
        for i, item in enumerate(suggestions):
            text = item["text"]
            item_type = item["type"]
            
            # Format based on type
            if item_type == "keyword":
                text = f"🔑 {text}"
            elif item_type == "function":
                text = f"🔧 {text}()"
            elif item_type == "variable":
                text = f"📌 {text}"
            elif item_type == "struct":
                text = f"📦 {text}"
            elif item_type == "enum":
                text = f"📋 {text}"
            elif item_type == "preprocessor":
                text = f"⚙️ {text}"
            elif item_type == "header":
                text = f"📄 {text}"
            elif item_type == "member":
                text = f"🔹 {text}"
            elif item_type == "snippet":
                text = f"✂️ {text}"
            
            listbox.insert(tk.END, text)
        
        # Select first item by default
        if suggestions:
            listbox.selection_set(0)
        
        # Add description frame
        desc_frame = tk.Frame(
            self.suggestion_window,
            bg=get_color("bg_tertiary"),
            height=60
        )
        
        desc_label = tk.Label(
            desc_frame,
            text="",
            bg=get_color("bg_tertiary"),
            fg=get_color("fg_primary"),
            font=("Arial", 10),
            anchor="w",
            justify="left",
            wraplength=400,
            padx=5,
            pady=5
        )
        desc_label.pack(fill="both", expand=True)
        
        # Update description on selection change
        def on_select(event):
            selected = listbox.curselection()
            if selected:
                index = selected[0]
                if 0 <= index < len(suggestions):
                    selected_item = suggestions[index]
                    desc_text = selected_item["desc"]
                    
                    if "signature" in selected_item:
                        desc_text = f"{selected_item['signature']}\n{desc_text}"
                    
                    desc_label.config(text=desc_text)
        
        listbox.bind("<<ListboxSelect>>", on_select)
        listbox.bind("<Return>", lambda e: self._complete_selection(suggestions, listbox))
        listbox.bind("<Double-Button-1>", lambda e: self._complete_selection(suggestions, listbox))
        
        # Pack the widgets
        listbox.pack(fill="both", expand=True)
        desc_frame.pack(fill="x")
        
        # Trigger initial description display
        on_select(None)
        
        # Store suggestions for future use
        self.current_suggestions = suggestions
    
    def _show_param_info_window(self, func_name, signature, description):
        """Display parameter information window"""
        # Close existing window
        if self.param_info_window:
            self.param_info_window.destroy()
        
        # Get cursor position on screen
        cursor_pos = self.editor.index(tk.INSERT)
        line, col = map(int, cursor_pos.split('.'))
        x, y, width, height = self.editor._textbox.bbox(cursor_pos)
        
        # Convert to screen coordinates
        x_screen = self.editor.winfo_rootx() + x
        y_screen = self.editor.winfo_rooty() + y
        
        # Create parameter info window
        self.param_info_window = tk.Toplevel(self.editor)
        self.param_info_window.wm_overrideredirect(True)  # No window decorations
        self.param_info_window.wm_geometry(f"+{x_screen}+{y_screen-50}")  # Position above cursor
        
        # Configure window appearance
        self.param_info_window.configure(bg=get_color("bg_tertiary"))
        
        # Create a frame for the parameter info
        info_frame = tk.Frame(
            self.param_info_window,
            bg=get_color("bg_tertiary"),
            bd=1,
            relief="solid"
        )
        info_frame.pack(padx=2, pady=2)
        
        # Function name label
        func_label = tk.Label(
            info_frame,
            text=func_name,
            bg=get_color("bg_tertiary"),
            fg=get_color("function"),
            font=("Cascadia Code", 11, "bold"),
            anchor="w",
            padx=5,
            pady=2
        )
        func_label.pack(fill="x")
        
        # Signature label
        self.signature_label = tk.Label(
            info_frame,
            text=signature,
            bg=get_color("bg_tertiary"),
            fg=get_color("fg_primary"),
            font=("Cascadia Code", 10),
            anchor="w",
            padx=5,
            pady=2
        )
        self.signature_label.pack(fill="x")
        
        # Description label
        if description:
            desc_label = tk.Label(
                info_frame,
                text=description,
                bg=get_color("bg_tertiary"),
                fg=get_color("fg_secondary"),
                font=("Arial", 9),
                anchor="w",
                justify="left",
                wraplength=400,
                padx=5,
                pady=2
            )
            desc_label.pack(fill="x")
        
        # Store signature for parameter highlighting
        self.current_signature = signature
        self.current_param_index = 0
        
        # Highlight the first parameter
        self._highlight_current_param(0)
    
    def _highlight_current_param(self, param_index):
        """Highlight the current parameter in the signature"""
        if not hasattr(self, "signature_label") or not self.signature_label:
            return
            
        # Extract parameters part from signature
        signature = self.current_signature
        
        # Find opening and closing parentheses
        open_paren = signature.find('(')
        close_paren = signature.rfind(')')
        
        if open_paren >= 0 and close_paren > open_paren:
            params_text = signature[open_paren+1:close_paren]
            
            # Split by commas (accounting for nested parentheses in complex types)
            params = []
            current_param = ""
            nesting_level = 0
            
            for char in params_text:
                if char == ',' and nesting_level == 0:
                    params.append(current_param.strip())
                    current_param = ""
                else:
                    current_param += char
                    if char == '(':
                        nesting_level += 1
                    elif char == ')':
                        nesting_level -= 1
            
            if current_param:
                params.append(current_param.strip())
            
            # Ensure param_index is valid
            if params and 0 <= param_index < len(params):
                self.current_param_index = param_index
                
                # Create a new signature text with the current parameter highlighted
                highlighted_signature = signature[:open_paren+1]
                
                for i, param in enumerate(params):
                    if i > 0:
                        highlighted_signature += ", "
                    
                    if i == param_index:
                        # Add highlighting tags (Tkinter doesn't directly support partial text coloring)
                        # We'll recreate the label with rich text
                        highlighted_signature += f"[{param}]"
                    else:
                        highlighted_signature += param
                
                highlighted_signature += signature[close_paren:]
                
                # Update the signature label
                self.signature_label.config(text=highlighted_signature)
    
    def _complete_selection(self, suggestions, listbox):
        """Complete the selected suggestion"""
        selected = listbox.curselection()
        if selected:
            index = selected[0]
            if 0 <= index < len(suggestions):
                # Get selected suggestion
                suggestion = suggestions[index]
                
                # Insert the suggestion
                self._insert_suggestion(suggestion)
                
                # Close the suggestion window
                self._dismiss_suggestions()
    
    def _try_complete_suggestion(self, event):
        """Try to complete current suggestion on Tab key"""
        if self.suggestion_window and hasattr(self, "current_suggestions"):
            # Get the listbox widget
            listbox = self.suggestion_window.winfo_children()[0]
            selected = listbox.curselection()
            
            if selected:
                index = selected[0]
                if 0 <= index < len(self.current_suggestions):
                    suggestion = self.current_suggestions[index]
                    self._insert_suggestion(suggestion)
                    self._dismiss_suggestions()
                    return "break"  # Prevent default tab behavior
        
        return None  # Allow default tab behavior
    
    def _insert_suggestion(self, suggestion):
        """Insert the selected suggestion at cursor position"""
        # Get current word and cursor position
        cursor_pos = self.editor.index(tk.INSERT)
        line, col = map(int, cursor_pos.split('.'))
        line_text = self.editor.get(f"{line}.0", f"{line}.{col}")
        
        # Find word start position
        word_start = col
        for i in range(col-1, -1, -1):
            if i < len(line_text) and not (line_text[i].isalnum() or line_text[i] == '_'):
                word_start = i + 1
                break
        
        # Replace current word with suggestion
        text = suggestion["text"]
        self.editor.delete(f"{line}.{word_start}", f"{line}.{col}")
        
        # Handle different types of suggestions
        if suggestion["type"] == "function":
            # Add parentheses for functions
            self.editor.insert(f"{line}.{word_start}", f"{text}()")
            # Position cursor between parentheses
            self.editor.mark_set(tk.INSERT, f"{line}.{word_start + len(text) + 1}")
        elif suggestion["type"] == "snippet":
            # Insert snippet code
            code = suggestion["code"]
            
            # Calculate indentation
            indent_match = re.match(r'^(\s*)', line_text)
            indent = indent_match.group(1) if indent_match else ""
            
            # Apply indentation to each line
            indented_code = '\n'.join([indent + line if i > 0 else line 
                                      for i, line in enumerate(code.split('\n'))])
            
            # Delete current line and insert snippet
            self.editor.delete(f"{line}.0", f"{line}.0 lineend")
            self.editor.insert(f"{line}.0", indented_code)
            
            # Position cursor at a logical place (after first parentheses or at indented line)
            cursor_pos = indented_code.find("{}") + 1 if "{}" in indented_code else indented_code.find(");") + 1
            if cursor_pos > 0:
                self.editor.mark_set(tk.INSERT, f"{line}.{cursor_pos}")
            else:
                # Find first indented line
                code_lines = indented_code.split('\n')
                if len(code_lines) > 1:
                    first_line = code_lines[0]
                    second_line = code_lines[1]
                    
                    # Position cursor at indentation on second line plus one tab
                    indent_len = len(second_line) - len(second_line.lstrip())
                    self.editor.mark_set(tk.INSERT, f"{line+1}.{indent_len + 4}")
        else:
            # For other types, just insert the text
            self.editor.insert(f"{line}.{word_start}", text)
    
    def _get_current_word(self, line_text):
        """Extract the current word being typed"""
        # Find last non-word character
        match = re.search(r'[^\w_]*(\w*)$', line_text)
        if match:
            return match.group(1)
        return ""
    
    def _update_suggestions(self):
        """Update suggestions window position and content"""
        if self.suggestion_window:
            # Get current cursor position
            cursor_pos = self.editor.index(tk.INSERT)
            line, col = map(int, cursor_pos.split('.'))
            x, y, width, height = self.editor._textbox.bbox(cursor_pos)
            
            # Convert to screen coordinates
            x_screen = self.editor.winfo_rootx() + x
            y_screen = self.editor.winfo_rooty() + y + height
            
            # Update window position
            self.suggestion_window.wm_geometry(f"+{x_screen}+{y_screen}")
            
            # Update suggestions content if needed
            current_word = self._get_current_word(self.editor.get(f"{line}.0", f"{line}.{col}"))
            if current_word:
                # Filter suggestions based on current word
                filtered = [s for s in self.current_suggestions 
                          if s["text"].lower().startswith(current_word.lower())]
                
                if filtered and filtered != self.current_suggestions:
                    # Update listbox with filtered suggestions
                    listbox = self.suggestion_window.winfo_children()[0]
                    listbox.delete(0, tk.END)
                    
                    for item in filtered:
                        text = item["text"]
                        item_type = item["type"]
                        
                        # Format based on type
                        if item_type == "keyword":
                            text = f"🔑 {text}"
                        elif item_type == "function":
                            text = f"🔧 {text}()"
                        elif item_type == "variable":
                            text = f"📌 {text}"
                        elif item_type == "struct":
                            text = f"📦 {text}"
                        elif item_type == "enum":
                            text = f"📋 {text}"
                        elif item_type == "preprocessor":
                            text = f"⚙️ {text}"
                        elif item_type == "header":
                            text = f"📄 {text}"
                        elif item_type == "member":
                            text = f"🔹 {text}"
                        elif item_type == "snippet":
                            text = f"✂️ {text}"
                        
                        listbox.insert(tk.END, text)
                    
                    # Select first item
                    if filtered:
                        listbox.selection_set(0)
                    
                    # Update stored suggestions
                    self.current_suggestions = filtered
    
    def _dismiss_suggestions(self, event=None):
        """Close the suggestions window"""
        if self.suggestion_window:
            self.suggestion_window.destroy()
            self.suggestion_window = None
            self.current_suggestions = []
        return None  # Allow default handling
    
    def _dismiss_param_info(self, event=None):
        """Close the parameter info window"""
        if self.param_info_window:
            self.param_info_window.destroy()
            self.param_info_window = None
        return None  # Allow default handling
    
    def scan_current_file(self):
        """
        Scan the current file for symbols to enable better intellisense
        """
        if not self.editor:
            return
        
        content = self.editor.get("1.0", "end-1c")
        
        # Clear existing file-specific symbols
        file_symbols = {
            "variables": {},
            "functions": {},
            "structs": {},
            "enums": {},
            "typedefs": {}
        }
        
        # Scan for variable declarations
        var_pattern = r'(int|char|float|double|long|short|unsigned|signed|struct\s+\w+|enum\s+\w+|\w+)\s+\*?(\w+)(?:\[.*\])?(?:\s*=\s*.+)?;'
        for match in re.finditer(var_pattern, content):
            var_type = match.group(1)
            var_name = match.group(2)
            file_symbols["variables"][var_name] = var_type
        
        # Scan for function declarations/definitions
        func_pattern = r'(int|void|char|float|double|long|short|unsigned|signed|struct\s+\w+|enum\s+\w+|\w+)\s+(\w+)\s*\((.*)\)'
        for match in re.finditer(func_pattern, content):
            return_type = match.group(1)
            func_name = match.group(2)
            params_text = match.group(3)
            
            # Parse parameters
            params = []
            if params_text.strip() and params_text.strip() != "void":
                param_parts = params_text.split(',')
                for part in param_parts:
                    part = part.strip()
                    if part:
                        # Extract parameter type and name
                        param_match = re.match(r'(.*?)(\w+)(?:\[.*\])?$', part)
                        if param_match:
                            param_type = param_match.group(1).strip()
                            param_name = param_match.group(2).strip()
                            params.append({"type": param_type, "name": param_name})
            
            file_symbols["functions"][func_name] = {
                "return_type": return_type,
                "params": params
            }
        
        # Scan for struct definitions
        struct_pattern = r'struct\s+(\w+)\s*\{([^}]*)\}'
        for match in re.finditer(struct_pattern, content):
            struct_name = match.group(1)
            struct_body = match.group(2)
            
            # Parse struct members
            members = {}
            for line in struct_body.split(';'):
                line = line.strip()
                if line:
                    # Extract member type and name
                    member_match = re.match(r'(.*?)(\w+)(?:\[.*\])?$', line)
                    if member_match:
                        member_type = member_match.group(1).strip()
                        member_name = member_match.group(2).strip()
                        members[member_name] = member_type
            
            file_symbols["structs"][struct_name] = {"members": members}
        
        # Scan for enum definitions
        enum_pattern = r'enum\s+(\w+)\s*\{([^}]*)\}'
        for match in re.finditer(enum_pattern, content):
            enum_name = match.group(1)
            enum_body = match.group(2)
            
            # Parse enum values
            values = {}
            for i, item in enumerate(enum_body.split(',')):
                item = item.strip()
                if item:
                    if '=' in item:
                        name, value = item.split('=', 1)
                        values[name.strip()] = value.strip()
                    else:
                        values[item] = i
            
            file_symbols["enums"][enum_name] = {"values": values}
        
        # Scan for typedef statements
        typedef_pattern = r'typedef\s+(.*?)\s+(\w+);'
        for match in re.finditer(typedef_pattern, content):
            original = match.group(1)
            alias = match.group(2)
            file_symbols["typedefs"][alias] = original
        
        # Update project symbols with file symbols
        for category in file_symbols:
            self.project_symbols[category].update(file_symbols[category])
    
    def scan_project_files(self):
        """
        Scan all C files in the project for symbols
        """
        if "current_directory" in self.state:
            dir_path = self.state["current_directory"]
            
            try:
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        if file.endswith('.c') or file.endswith('.h'):
                            file_path = os.path.join(root, file)
                            self._scan_file(file_path)
            except Exception:
                pass
    
    def _scan_file(self, file_path):
        """
        Scan a single file for symbols
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Use same scanning logic as scan_current_file, but store in project symbols
            # This simplified version only scans for function and struct definitions
            
            # Scan for function declarations/definitions
            func_pattern = r'(int|void|char|float|double|long|short|unsigned|signed|struct\s+\w+|enum\s+\w+|\w+)\s+(\w+)\s*\((.*)\)'
            for match in re.finditer(func_pattern, content):
                return_type = match.group(1)
                func_name = match.group(2)
                params_text = match.group(3)
                
                # Skip if already in project symbols
                if func_name in self.project_symbols["functions"]:
                    continue
                
                # Parse parameters simplified
                params = []
                if params_text.strip() and params_text.strip() != "void":
                    param_parts = params_text.split(',')
                    for part in param_parts:
                        part = part.strip()
                        if part:
                            params.append({"type": "param", "name": part})
                
                self.project_symbols["functions"][func_name] = {
                    "return_type": return_type,
                    "params": params,
                    "desc": f"From {os.path.basename(file_path)}"
                }
            
            # Simplified struct scanning
            struct_pattern = r'struct\s+(\w+)\s*\{([^}]*)\}'
            for match in re.finditer(struct_pattern, content):
                struct_name = match.group(1)
                
                # Skip if already in project symbols
                if struct_name in self.project_symbols["structs"]:
                    continue
                
                self.project_symbols["structs"][struct_name] = {
                    "members": {},
                    "desc": f"From {os.path.basename(file_path)}"
                }
                
        except Exception:
            pass
