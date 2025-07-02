
import logging
import os
from pathlib import Path

from app.core.config import APP_DATA_ROOT_DIR, APP_NAME 

def configure_logging():
    """
    Configures application-wide logging to both console and a file.
    The log file is placed in the application's data directory.
    """
    log_dir = APP_DATA_ROOT_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True) # Ensure the log directory exists

    log_file_path = log_dir / f"{APP_NAME.lower()}.log"

    # Define a custom formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO) # Default console level

    # File handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO) # Default file level

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO) # Overall minimum logging level

    # Clear existing handlers to prevent duplicate logs if called multiple times
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Set specific log levels for libraries if needed (e.g., to reduce verbosity)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("nltk").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING) # Reduce asyncio verbosity

    logger = logging.getLogger(f"{APP_NAME}.core.logging")
    logger.info(f"Logging configured. Logs are saved to: {log_file_path}")