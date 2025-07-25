# desktop_app/utils/tray.py
import platform
import sys
import webbrowser
from pathlib import Path
from PIL import Image
import pystray
from pystray import MenuItem as Item
from app.core.config import APP_NAME
import asyncio # Import asyncio
import logging # Import logging

logger = logging.getLogger(f"{APP_NAME}.tray") # Add a logger for tray operations

class TrayManager:
    def __init__(self, on_open_settings, on_open_models, on_stop_server):
        self.icon = None
        self.on_open_settings = on_open_settings
        self.on_open_models = on_open_models
        self.on_stop_server = on_stop_server

    def _create_icon(self):
        icon_path = Path(__file__).parent.parent / "assets" / "images" / "logo.png"
        image = Image.open(icon_path) if icon_path.exists() else None

        menu = pystray.Menu(
            Item("Launch tool (http://localhost:7860/docs)", lambda icon, _: webbrowser.open("http://localhost:7860/docs")),
            Item("Settings", lambda icon, _: self.on_open_settings()),
            Item("Manage Models", lambda icon, _: self.on_open_models()),
            Item("Stop Server", lambda icon, _: self._shutdown()),
        )

        self.icon = pystray.Icon(APP_NAME, image, APP_NAME, menu)

    def _shutdown(self):
        logger.info("TrayManager: Initiating shutdown.")
        if self.icon:
            self.icon.stop() # Stop the pystray icon thread

        try:
            # Ensure the async callback is run.
            # If there's an existing loop, use it; otherwise, create a new one.
            # This is critical for calling an async function from a sync context.
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # No running event loop, create a new one for this task
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run the async stop server callback to completion
            loop.run_until_complete(self.on_stop_server())
            logger.info("TrayManager: Async stop_server callback completed.")

        except Exception as e:
            logger.error(f"TrayManager: Error during async shutdown callback: {e}", exc_info=True)
        finally:
            logger.info("TrayManager: Exiting process.")
            sys.exit(0) # Exit the script after the server has (attempted to) stop

    def show(self):
        self._create_icon()
        if platform.system() == "Darwin":
            # On macOS, pystray.run() blocks the main thread, which is fine
            # for a background runner that primarily manages the tray.
            self.icon.run()
        else:
            # For other platforms, run in a separate thread if main thread needs to do other things
            # self.icon.run_threaded() # You might need this if you add more async tasks to background_runner
            self.icon.run() # Sticking to run() for now as it's a dedicated background process