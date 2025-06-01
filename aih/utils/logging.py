"""
Logging configuration for AI-Horizon pipeline.

Provides structured logging with multiple output destinations.
"""

import sys
from pathlib import Path
from loguru import logger
from aih.config import settings, get_logs_path

def setup_logging(log_level: str = None) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Override the default log level
    """
    level = log_level or settings.log_level
    
    # Remove default handler
    logger.remove()
    
    # Console handler with colored output
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True
    )
    
    # File handler for all logs
    logs_path = get_logs_path()
    logger.add(
        logs_path / "aih_pipeline.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="1 month",
        compression="zip"
    )
    
    # Error log file
    logger.add(
        logs_path / "errors.log", 
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="5 MB",
        retention="3 months"
    )
    
    # API calls log (for monitoring usage)
    logger.add(
        logs_path / "api_calls.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {extra[api_type]} | {extra[tokens]:.0f} | {extra[cost]:.4f} | {message}",
        level="INFO",
        filter=lambda record: "api_call" in record["extra"],
        rotation="50 MB",
        retention="6 months"
    )

def get_logger(name: str):
    """Get a logger instance for a specific module."""
    return logger.bind(name=name)

def log_api_call(api_type: str, prompt: str, response: str, tokens: int, cost: float) -> None:
    """
    Log API call details for monitoring and analysis.
    
    Args:
        api_type: Type of API (perplexity, openai, anthropic)
        prompt: The input prompt
        response: The API response
        tokens: Number of tokens used
        cost: Estimated cost of the call
    """
    logger.bind(
        api_call=True,
        api_type=api_type,
        tokens=tokens,
        cost=cost
    ).info(f"API call: {prompt[:100]}... -> {response[:100]}...")

# Initialize logging on import
setup_logging() 