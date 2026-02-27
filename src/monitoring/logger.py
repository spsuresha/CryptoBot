"""
Logging configuration for the trading bot.
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from ..config.settings import Settings
from ..config.constants import LOG_FORMAT, LOG_DATE_FORMAT


def setup_logging(settings: Optional[Settings] = None) -> None:
    """
    Configure logging for the application.

    Args:
        settings: Application settings
    """
    settings = settings or Settings()

    # Create logs directory
    logs_dir = Path(settings.project_root) / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Get log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    if settings.log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handlers
    if settings.log_to_file:
        max_bytes = settings.max_log_file_size_mb * 1024 * 1024

        # Main log file
        main_handler = RotatingFileHandler(
            logs_dir / "main.log",
            maxBytes=max_bytes,
            backupCount=settings.log_backup_count
        )
        main_handler.setLevel(log_level)
        main_handler.setFormatter(formatter)
        root_logger.addHandler(main_handler)

        # Trading log file (INFO and above)
        trading_handler = RotatingFileHandler(
            logs_dir / "trading.log",
            maxBytes=max_bytes,
            backupCount=settings.log_backup_count
        )
        trading_handler.setLevel(logging.INFO)
        trading_handler.setFormatter(formatter)
        trading_logger = logging.getLogger("trading")
        trading_logger.addHandler(trading_handler)

        # Error log file (ERROR and above)
        error_handler = RotatingFileHandler(
            logs_dir / "errors.log",
            maxBytes=max_bytes,
            backupCount=settings.log_backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

    logging.info("Logging system initialized")
    logging.info(f"Log level: {settings.log_level}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
