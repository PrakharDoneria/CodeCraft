import customtkinter as ctk
from ui.theme import setup_theme
from ui.widgets import create_editor, create_output, create_menu, create_status_bar
from utils.highlighter import highlight

app = ctk.CTk()
app.geometry("1200x750")
app.title("ChiX - C Code Editor & Runner")

setup_theme()

# Shared state
state = {
    "current_file": None,
    "editor": None,
    "output": None,
    "app": app,
    "line_numbers": None,
    "status_bar": None,
    "mode": "compiler",  # Default mode is compiler
}

# === Toolbar Menu (Top) ===
create_menu(app, state)

# === Main Frame (Editor + Output) ===
main_frame = ctk.CTkFrame(app)
main_frame.pack(fill="both", expand=True)

# === Code Editor (Middle) with line numbers ===
state["editor"] = create_editor(main_frame, state)

# === Output Console (Bottom) ===
state["output"] = create_output(main_frame)

# === Status Bar (Bottom) ===
state["status_bar"] = create_status_bar(app, state)

# === Default Template ===
starter = """#include <stdio.h>

int main() {
    int x;
    printf("Enter a number: ");
    scanf("%d", &x);
    printf("You entered: %d\\n", x);
    return 0;
}
"""
state["editor"].insert("1.0", starter)
highlight(state["editor"])

# === Application info ===
credits = "ChiX Editor by Prakhar Doneria | Open Source: github.com/PrakharDoneria/ChiX"
state["status_bar"].set_credits(credits)

app.mainloop()