import subprocess
import os

def check_gcc_installed():
    """Check if GCC is installed and available in PATH"""
    try:
        subprocess.run(['gcc', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

def compile_c_code(source_path, output_path):
    """
    Compiles a C source file using GCC and returns compilation status and output message.

    Args:
        source_path (str): Path to the C source file.
        output_path (str): Path for the output executable.

    Returns:
        (bool, str): (True, success_message) if compiled successfully,
                     (False, error_message) if compilation failed.
    """
    if not os.path.exists(source_path):
        return False, "[ERROR] Source file not found."

    # Remove previous executable if exists
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except Exception as e:
            return False, f"[ERROR] Could not remove previous executable: {e}"

    try:
        # Compile with warnings and non-colored error output
        result = subprocess.run(
            ['gcc', '-Wall', '-Wextra', '-fdiagnostics-color=never', source_path, '-o', output_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        output = "\n".join(filter(None, [stdout, stderr]))

        if result.returncode == 0:
            return True, "[SUCCESS] Compilation completed. Running program..."
        else:
            return False, f"[ERROR] Compilation failed:\n{output}"

    except Exception as e:
        return False, f"[ERROR] Compilation process failed:\n{str(e)}"
