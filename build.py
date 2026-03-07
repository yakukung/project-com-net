import os
import platform
import subprocess
import sys

def build():
    # Detect OS
    current_os = platform.system()
    print(f"Detected OS: {current_os}")

    # General PyInstaller arguments
    # Collect all for customtkinter which is often needed
    common_args = [
        "--noconfirm",
        "--clean",
        "--collect-all", "customtkinter",
    ]

    print("--- Building Client ---")
    client_args = common_args + [
        "--name", f"ChatClient_{current_os}",
        "--windowed", # No console window for the client UI
    ]
    
    # If there are specific icons, we can add them here:
    # if current_os == "Windows":
    #     client_args.extend(["--icon", "client/assets/icon.ico"])
    
    client_cmd = [sys.executable, "-m", "PyInstaller"] + client_args + ["run_client.py"]
    subprocess.run(client_cmd, check=True)

    print("--- Building Server ---")
    server_args = common_args + [
        "--name", f"ChatServer_{current_os}",
        # Server usually needs a console
    ]
    
    server_cmd = [sys.executable, "-m", "PyInstaller"] + server_args + ["run_server.py"]
    subprocess.run(server_cmd, check=True)

    print(f"\nBuild complete for {current_os}! Executables are located in the 'dist' folder.")

if __name__ == "__main__":
    build()
