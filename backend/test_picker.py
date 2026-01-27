import subprocess
import sys

def open_dialog():
    print("Attempting to open dialog...")
    cmd = [
        "osascript",
        "-e",
        'POSIX path of (choose folder with prompt "Select Project Folder")'
    ]
    
    try:
        # check_output returns bytes
        result = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode('utf-8').strip()
        print(f"Result: {result}")
        if not result:
             return ""
        return result
    except subprocess.CalledProcessError as e:
        # User likely cancelled (non-zero exit code)
        print("User cancelled or osascript failed.")
        print(f"Error code: {e.returncode}")
        print(f"Stderr: {e.stderr}")
        return ""
    except Exception as e:
        print(f"Exception: {e}")
        return ""

if __name__ == "__main__":
    open_dialog()
