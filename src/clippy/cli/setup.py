"""Setup utilities for CLI: environment and logging configuration."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv


def load_env() -> None:
    """Load environment variables from .env file."""
    # Check current directory first
    if Path(".env").exists():
        load_dotenv(".env")
    # Then check home directory
    elif Path.home().joinpath(".clippy.env").exists():
        load_dotenv(Path.home() / ".clippy.env")


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application.

    Logs are written to:
    - Console (stderr): WARNING level by default, DEBUG with --verbose
    - File: ~/.clippy/logs/clippy.log (always DEBUG level)
    """
    console_level = logging.DEBUG if verbose else logging.WARNING

    # Create log directory
    log_dir = Path.home() / ".clippy" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "clippy.log"

    # Create formatters
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)

    # File handler (rotating, always DEBUG)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10_000_000,  # 10MB
        backupCount=5,  # Keep last 5 log files
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to DEBUG so file handler gets everything
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Set library loggers to WARNING to reduce noise
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
