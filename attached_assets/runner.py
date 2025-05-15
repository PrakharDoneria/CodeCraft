import os
import platform
import subprocess
from compiler.compiler import compile_c_code, check_gcc_installed
from core.interpreter import interpret_c_code

def run_code(state, mode="compiler"):
    """
    Runs the code using either a compiler or an interpreter based on the selected mode.

    Args:
        state (dict): The application state containing the editor and output widgets.
        mode (str): The mode of execution - "compiler" or "interpreter".
    """
    code = state["editor"].get("1.0", "end-1c")
    state["output"].delete("1.0", "end")

    if mode == "interpreter":
        # Use interpreter to execute the code
        success, msg = interpret_c_code(code)
        state["output"].insert("1.0", msg)
        return

    # Default to compiler if mode is not "interpreter"
    if not check_gcc_installed():
        state["output"].insert("1.0", "[ERROR] GCC (MinGW) is not installed or not in PATH.")
        return

    os.makedirs("temp", exist_ok=True)
    src = os.path.join("temp", "program.c")
    exe = os.path.join("temp", "program.exe")

    with open(src, "w") as f:
        f.write(code)

    success, msg = compile_c_code(src, exe)
    state["output"].insert("1.0", msg)

    if success:
        if platform.system() == "Windows":
            subprocess.Popen(f'start cmd /k "{exe}"', shell=True)
        else:
            subprocess.Popen(['x-terminal-emulator', '-e', exe])