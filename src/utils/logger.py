"""
Centralized logging utility for EduHyperRAG system.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from src.config import config

def get_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    """
    Creates and configures a logger instance.
    
    Args:
        name: Name of the module requesting the logger.
        log_file: Optional file path to store logs.
        
    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if already configured
    if logger.hasHandlers():
        return logger

    level = getattr(logging, config.log_level.upper(), logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional File Handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
