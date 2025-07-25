import subprocess
import asyncio
import sys
from pathlib import Path
from app.core.config import LOCAL_API_HOST, LOCAL_API_PORT
from app.core.logging import configure_logging # Assuming configure_logging is present and works
import logging

logger = logging.getLogger("desktop_app.server")
# configure_logging() # This is typically called once at app startup, e.g., in background_runner.py's main_background_runner

project_root = Path(__file__).parent.parent.parent
server_process = None

def is_server_running():
    # Use poll() to check if the subprocess has terminated. None means it's still running.
    return server_process is not None and server_process.poll() is None

async def start_server():
    global server_process
    if is_server_running():
        logger.info("Server already running.")
        return "already_running"

    server_command = [
        sys.executable, "-m", "uvicorn", "app.main:app",
        "--host", LOCAL_API_HOST, "--port", str(LOCAL_API_PORT), "--log-level", "info"
    ]
    
    logger.info(f"Attempting to start server with command: {' '.join(server_command)}")

    try:
        server_process = subprocess.Popen(
            server_command, cwd=project_root,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            bufsize=1 # Line-buffered output
        )
        logger.info(f"Server subprocess started with PID: {server_process.pid}")

        # Give the server a moment to start and check if it failed immediately
        await asyncio.sleep(2)

        if server_process.poll() is not None:
            # Server process terminated quickly, implies failure
            out, err = server_process.communicate() # Collect any output
            logger.error(f"Server process (PID: {server_process.pid}) failed to start immediately. Return code: {server_process.returncode}")
            if out: logger.error(f"Server STDOUT:\n{out}")
            if err: logger.error(f"Server STDERR:\n{err}")
            server_process = None
            return "failed"
        
        logger.info("Server started successfully.")
        return "success"
    except Exception as e:
        logger.error(f"Exception during server startup: {e}", exc_info=True)
        server_process = None
        return "failed_exception"

async def stop_server():
    global server_process
    if not is_server_running():
        logger.info("Server is not running, no need to stop.")
        return

    pid = server_process.pid
    logger.info(f"Attempting to stop server process with PID: {pid}...")

    try:
        logger.info(f"Sending SIGTERM to PID {pid}...")
        server_process.terminate() # Send SIGTERM
        await asyncio.to_thread(server_process.wait, timeout=5) # Wait for it to terminate

        if server_process.poll() is None: # If it's still running after terminate()
            logger.warning(f"Server with PID {pid} did not terminate gracefully after SIGTERM within timeout. Sending SIGKILL...")
            server_process.kill() # Send SIGKILL
            await asyncio.to_thread(server_process.wait, timeout=5) # Wait again for forceful kill

        if server_process.poll() is None:
            logger.error(f"Server with PID {pid} is still running after SIGKILL. Manual intervention might be needed. Check for orphaned processes.")
            return "failed_kill"
        else:
            logger.info(f"Server with PID {pid} stopped successfully. Return code: {server_process.returncode}")
            return "success"

    except Exception as e:
        logger.error(f"Error stopping server with PID {pid}: {e}", exc_info=True)
        return "failed_exception"
    finally:
        server_process = None # Clear the reference regardless of success/failure