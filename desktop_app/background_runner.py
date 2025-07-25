import asyncio
import sys
import os
import logging
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from desktop_app.utils.server import start_server, stop_server, is_server_running
from desktop_app.utils.tray import TrayManager
from app.core.config import APP_NAME
from app.core.logging import configure_logging

logger = logging.getLogger(f"{APP_NAME}.background_runner")

# Configure logging at the very start of the background process
configure_logging()

# Global variable to hold the event loop reference
# This is crucial for scheduling tasks from other threads (like pystray's)
global_event_loop = None

async def main_background_task():
    global global_event_loop
    global_event_loop = asyncio.get_running_loop() # Get the loop that this async function is running in

    logger.info("Background runner started.")

    # Start the server
    if not is_server_running():
        logger.info("Attempting to start server from background runner...")
        result = await start_server()
        if result == "success":
            logger.info("Server started successfully by background runner.")
        elif result == "already_running":
            logger.info("Server was already running.")
        else:
            logger.error(f"Failed to start server from background runner: {result}")
            # Consider exiting if server cannot start, or implement retry logic
            sys.exit(1)
    else:
        logger.info("Server already running.")

    # Tray icon actions (placeholders for now, you might need inter-process communication)
    # These lambda functions would ideally trigger actions in the main Flet app
    # or expose endpoints on the local server that the main app can call.
    # For now, they can just log or perform simple actions.
    def open_settings_placeholder():
        logger.info("Open settings triggered from tray (background).")
        import webbrowser
        webbrowser.open("http://localhost:7860/settings") # Example for server-based settings

    def open_models_placeholder():
        logger.info("Open models triggered from tray (background).")
        import webbrowser
        webbrowser.open("http://localhost:7860/models") # Example for server-based model management

    async def stop_server_and_exit_async_task():
        """This is the actual async task that will stop the server and exit."""
        logger.info("Stop server and exit task initiated from tray.")
        await stop_server() # Await the actual server stop
        if tray_manager.icon:
            tray_manager.icon.stop() # Stop the tray icon
        logger.info("Server stopped, tray icon stopped. Exiting background runner.")
        sys.exit(0) # Exit the process

    # This is the synchronous callback for pystray.
    # It schedules the async task on the main event loop.
    def on_tray_stop_server_clicked():
        logger.info("Tray 'Stop Server' clicked. Scheduling async shutdown.")
        if global_event_loop and global_event_loop.is_running():
            # Schedule the async task to run on the main event loop
            global_event_loop.call_soon_threadsafe(
                asyncio.create_task, stop_server_and_exit_async_task()
            )
        else:
            logger.error("No running event loop found to schedule server stop. Server might not stop gracefully.")
            # Fallback for unexpected scenarios: try to stop directly (less graceful)
            # This path should ideally not be hit if the loop is managed correctly.
            try:
                asyncio.run(stop_server_and_exit_async_task())
            except RuntimeError as e:
                logger.error(f"Failed to stop server directly (no running loop): {e}")
                sys.exit(1) # Force exit if cannot stop gracefully


    # Initialize and show tray icon
    tray_manager = TrayManager(
        on_open_settings=open_settings_placeholder,
        on_open_models=open_models_placeholder,
        on_stop_server=on_tray_stop_server_clicked # Pass the synchronous scheduler
    )
    # The run() method for pystray will block if not detached.
    # Since this is a dedicated background process, `run()` is fine.
    # For macOS, run_detached() might still be necessary depending on context.
    tray_manager.show()
    logger.info("Tray icon shown. Background runner is active.")

if __name__ == "__main__":
    try:
        asyncio.run(main_background_task())
    except KeyboardInterrupt:
        logger.info("Background runner interrupted. Shutting down.")
        # Attempt to stop server gracefully on Ctrl+C during development
        if global_event_loop and global_event_loop.is_running():
            global_event_loop.run_until_complete(stop_server())
        else:
            # Fallback if loop is already closed or not running
            asyncio.run(stop_server())