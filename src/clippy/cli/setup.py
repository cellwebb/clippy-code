"""Setup utilities for CLI: environment and logging configuration."""

import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


def _cleanup_old_logs(log_dir: Path, keep: int = 20) -> None:
    """Remove old log files, keeping only the most recent N files.

    Args:
        log_dir: Directory containing log files
        keep: Number of most recent log files to keep (default: 20)
    """
    try:
        # Get all clippy log files sorted by modification time (newest first)
        log_files = sorted(
            log_dir.glob("clippy-*.log"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        # Remove old log files beyond the keep limit
        for old_log in log_files[keep:]:
            try:
                old_log.unlink()
            except Exception:
                # Ignore errors when deleting old logs
                pass
    except Exception:
        # Ignore errors in cleanup - not critical
        pass


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
    - File: ~/.clippy/logs/clippy-YYYY-MM-DD-HHMMSS.log (new file per session, always DEBUG level)
    """
    console_level = logging.DEBUG if verbose else logging.WARNING

    # Create log directory
    log_dir = Path.home() / ".clippy" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create timestamped log file for this session
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    log_file = log_dir / f"clippy-{timestamp}.log"

    # Clean up old log files, keep only the most recent 20
    _cleanup_old_logs(log_dir, keep=20)

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

    # File handler (new file per session, always DEBUG)
    file_handler = logging.FileHandler(
        log_file,
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
