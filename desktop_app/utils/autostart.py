import os
import sys
import platform
import subprocess
from pathlib import Path
import logging

from app.core.config import APP_NAME

logger = logging.getLogger(f"{APP_NAME}.autostart")

# Define the script that should be autostarted.
# This should point to your background_runner.py
BACKGROUND_RUNNER_SCRIPT_PATH = (Path(__file__).resolve().parent.parent / "background_runner.py")

def _get_executable_path():
    """Returns the path to the Python executable or the bundled executable."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as a PyInstaller bundle
        # For a bundled app, this needs to be the path to the main executable
        # which ideally should launch background_runner.
        # This can be complex with PyInstaller, often requiring a separate
        # bundled executable for the background process, or the main app
        # needs to spawn it correctly.
        # For simplicity here, we assume if bundled, the main executable itself
        # handles the initial spawn correctly, or BACKGROUND_RUNNER_SCRIPT
        # refers to a bundled script that PyInstaller makes executable.
        return sys.executable
    else:
        # Running as a script
        return sys.executable

def enable_autostart_windows():
    """
    Enables autostart on Windows by creating a registry entry.
    Runs the background_runner.py hidden.
    """
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key_name = APP_NAME.replace(".", "_") # Make it a valid registry key name

        # Path to the Python executable and the script
        # Using pythonw.exe ensures no console window
        python_exe = sys.executable.replace("python.exe", "pythonw.exe")
        if not os.path.exists(python_exe):
            python_exe = sys.executable # Fallback if pythonw.exe is not found

        # Command to run: pythonw.exe "path_to_background_runner.py"
        command = f'"{python_exe}" "{BACKGROUND_RUNNER_SCRIPT_PATH}"'

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, key_name, 0, winreg.REG_SZ, command)
        logger.info(f"Autostart enabled for Windows: {command}")
        return True
    except Exception as e:
        logger.error(f"Failed to enable autostart on Windows: {e}")
        return False

def disable_autostart_windows():
    """Disables autostart on Windows by removing the registry entry."""
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key_name = APP_NAME.replace(".", "_")
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, key_name)
                logger.info("Autostart disabled for Windows.")
                return True
            except FileNotFoundError:
                logger.info("Autostart entry not found for Windows (already disabled).")
                return True
    except Exception as e:
        logger.error(f"Failed to disable autostart on Windows: {e}")
        return False

def enable_autostart_macos():
    """
    Enables autostart on macOS by creating/updating and loading a Launch Agent (.plist file).
    """
    try:
        exe_path = _get_executable_path()
        runner_script_path = str(BACKGROUND_RUNNER_SCRIPT_PATH)

        plist_filename = f"{APP_NAME}.plist"
        plist_path = Path.home() / "Library" / "LaunchAgents" / plist_filename

        # --- IMPORTANT: Attempt to unload the service first for a clean state ---
        if plist_path.exists():
            # Use check=False because unload will fail if the service isn't currently loaded,
            # but we still want to proceed with writing/loading it.
            try:
                subprocess.run(["launchctl", "unload", str(plist_path)], check=True, capture_output=True)
                logger.info(f"Successfully unloaded existing autostart agent: {plist_path}")
            except subprocess.CalledProcessError as unload_e:
                # Log stderr output from launchctl for debugging if unload fails
                stderr_output = unload_e.stderr.decode().strip() if unload_e.stderr else ""
                logger.warning(f"Could not unload existing agent (might not be loaded): {unload_e.returncode} - {stderr_output}")
            except FileNotFoundError:
                logger.warning(f"launchctl command not found (macOS utility).")
        # -------------------------------------------------------------------------

        # Ensure the directory exists
        plist_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate the plist content
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{APP_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{exe_path}</string>
        <string>{runner_script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/{APP_NAME}.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/{APP_NAME}.stderr.log</string>
</dict>
</plist>"""
        # Write the plist file
        with open(plist_path, "w") as f:
            f.write(plist_content)
        logger.info(f"Wrote plist to: {plist_path}")

        # Ensure the background runner script itself is executable
        os.chmod(BACKGROUND_RUNNER_SCRIPT_PATH, 0o755)
        logger.info(f"Set executable permissions for: {BACKGROUND_RUNNER_SCRIPT_PATH}")

        # Load the agent immediately
        subprocess.run(["launchctl", "load", str(plist_path)], check=True, capture_output=True)
        logger.info(f"Autostart enabled for macOS: {plist_path}")
        return True
    except subprocess.CalledProcessError as e:
        # Capture stdout/stderr from the failing launchctl load command
        stdout_output = e.stdout.decode().strip() if e.stdout else ""
        stderr_output = e.stderr.decode().strip() if e.stderr else ""
        logger.error(f"Failed to enable autostart on macOS (launchctl error {e.returncode}):\nSTDOUT: {stdout_output}\nSTDERR: {stderr_output}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Failed to enable autostart on macOS: {e}", exc_info=True)
        return False

def disable_autostart_macos():
    """Disables autostart on macOS by unloading and deleting the Launch Agent."""
    try:
        plist_filename = f"{APP_NAME}.plist"
        plist_path = Path.home() / "Library" / "LaunchAgents" / plist_filename
        if plist_path.exists():
            subprocess.run(["launchctl", "unload", str(plist_path)], check=False, capture_output=True)
            plist_path.unlink()
            logger.info("Autostart disabled for macOS.")
            return True
        else:
            logger.info("Autostart entry not found for macOS (already disabled).")
            return True
    except Exception as e:
        logger.error(f"Failed to disable autostart on macOS: {e}")
        return False

def enable_autostart_linux():
    """
    Enables autostart on Linux using a Desktop Entry (.desktop file).
    """
    try:
        desktop_content = f"""[Desktop Entry]
Type=Application
Exec={_get_executable_path()} {BACKGROUND_RUNNER_SCRIPT_PATH}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name={APP_NAME}
Comment=Starts the {APP_NAME} background server.
Icon=
""" # You might want to specify an icon path here if you have one
        desktop_filename = f"{APP_NAME}.desktop"
        autostart_dir = Path.home() / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        desktop_file_path = autostart_dir / desktop_filename

        with open(desktop_file_path, "w") as f:
            f.write(desktop_content)
        os.chmod(desktop_file_path, 0o755) # Make it executable
        logger.info(f"Autostart enabled for Linux: {desktop_file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to enable autostart on Linux: {e}")
        return False

def disable_autostart_linux():
    """Disables autostart on Linux by deleting the Desktop Entry."""
    try:
        desktop_filename = f"{APP_NAME}.desktop"
        desktop_file_path = Path.home() / ".config" / "autostart" / desktop_filename
        if desktop_file_path.exists():
            desktop_file_path.unlink()
            logger.info("Autostart disabled for Linux.")
            return True
        else:
            logger.info("Autostart entry not found for Linux (already disabled).")
            return True
    except Exception as e:
        logger.error(f"Failed to disable autostart on Linux: {e}")
        return False

def enable_autostart():
    """Enables autostart based on the current platform."""
    current_platform = platform.system()
    if current_platform == "Windows":
        return enable_autostart_windows()
    elif current_platform == "Darwin":
        return enable_autostart_macos()
    elif current_platform == "Linux":
        return enable_autostart_linux()
    else:
        logger.warning(f"Autostart not supported on '{current_platform}'.")
        return False

def disable_autostart():
    """Disables autostart based on the current platform."""
    current_platform = platform.system()
    if current_platform == "Windows":
        return disable_autostart_windows()
    elif current_platform == "Darwin":
        return disable_autostart_macos()
    elif current_platform == "Linux":
        return disable_autostart_linux()
    else:
        logger.warning(f"Disable autostart not supported on '{current_platform}'.")
        return False