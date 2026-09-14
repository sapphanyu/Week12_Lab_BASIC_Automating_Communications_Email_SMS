"""
email-sms-automator/src/utils.py
Utility functions for logging, environment variable management, and directory operations.
"""

import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file into the runtime environment
load_dotenv()

# Configure basic fallback logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up and configures a logger for specific modules.
    Prevents adding duplicate handlers if called multiple times.

    :param name: Name of the logger (typically __name__).
    :param level: Logging severity level (default: logging.INFO).
    :return: Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    logger.propagate = False
    return logger



logger = setup_logging(__name__)


def get_env_variable(var_name: str) -> str:
    """
    Retrieves an environment variable, raising a ValueError if not found.

    :param var_name: Name of the environment variable.
    :return: String value of the environment variable.
    :raises ValueError: If the environment variable is not defined or is None.
    """
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(
            f"Environment variable '{var_name}' not set. Please check your .env file or environment settings."
        )
    return value


def ensure_directory_exists(path: str) -> None:
    """
    Ensures that a directory exists, creating it if necessary.

    :param path: Filesystem directory path to create/ensure.
    :raises OSError: If the directory cannot be created.
    """
    try:
        os.makedirs(path, exist_ok=True)
        logger.info(f"Directory ensured: {path}")
    except OSError as e:
        logger.error(f"Error creating directory {path}: {e}")
        raise
