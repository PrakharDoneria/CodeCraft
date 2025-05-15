import subprocess
import os

def interpret_c_code(code):
    """
    Interprets C code using an interpreter and returns the output or error.

    Args:
        code (str): The C code to interpret.

    Returns:
        (bool, str): (True, output_message) if executed successfully,
                     (False, error_message) if execution failed.
    """
    # Check if tcc is installed
    try:
        subprocess.run(['tcc', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except FileNotFoundError:
        return False, "[ERROR] Interpreter not available: 'tcc' is not installed or not in PATH. Please install Tiny C Compiler (tcc) and try again."

    os.makedirs("temp", exist_ok=True)
    src = os.path.join("temp", "program.c")

    # Write code to temporary file
    with open(src, "w") as f:
        f.write(code)

    try:
        # Use tcc to interpret the code
        result = subprocess.run(
            ['tcc', '-run', src],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        output = "\n".join(filter(None, [stdout, stderr]))

        if result.returncode == 0:
            return True, output
        else:
            return False, f"[ERROR] Interpretation failed:\n{output}"

    except Exception as e:
        return False, f"[ERROR] Interpretation process failed:\n{str(e)}"