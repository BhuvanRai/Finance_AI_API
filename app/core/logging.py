import sys
from loguru import logger

def setup_logging():
    # Remove default handler
    logger.remove()
    
    # Add stdout handler with color/formatting
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
    )
    
    # Optional: Add file handler for production logs
    # logger.add("logs/app.log", rotation="500 MB", level="INFO")
