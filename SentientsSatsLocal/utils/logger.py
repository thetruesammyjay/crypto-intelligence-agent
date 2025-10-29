"""
Logging Configuration for Crypto Intelligence Agent

Provides colored console output and file logging with rotation.
Uses coloredlogs for beautiful terminal output and standard logging for files.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional
import coloredlogs


class AgentLogger:
    """
    Custom logger for the Crypto Intelligence Agent.
    
    Features:
    - Colored console output (using coloredlogs)
    - File logging with rotation
    - Multiple log levels
    - Module-specific loggers
    """
    
    _loggers = {}
    _initialized = False
    
    @classmethod
    def setup(cls, 
              log_level: str = "INFO",
              log_to_file: bool = True,
              log_file_path: str = "./data/logs/agent.log",
              log_max_bytes: int = 10485760,  # 10 MB
              log_backup_count: int = 5,
              log_colored: bool = True) -> None:
        """
        Setup the logging system.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: Whether to log to file
            log_file_path: Path to log file
            log_max_bytes: Maximum size of log file before rotation
            log_backup_count: Number of backup files to keep
            log_colored: Use colored output in console
        """
        if cls._initialized:
            return
        
        # Create logs directory if it doesn't exist
        if log_to_file:
            log_dir = os.path.dirname(log_file_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Console handler with colored output
        if log_colored:
            coloredlogs.install(
                level=log_level.upper(),
                fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                level_styles={
                    'debug': {'color': 'cyan'},
                    'info': {'color': 'green'},
                    'warning': {'color': 'yellow', 'bold': True},
                    'error': {'color': 'red', 'bold': True},
                    'critical': {'color': 'red', 'bold': True, 'background': 'white'},
                },
                field_styles={
                    'asctime': {'color': 'blue'},
                    'levelname': {'color': 'white', 'bold': True},
                    'name': {'color': 'magenta'},
                }
            )
        else:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, log_level.upper()))
            console_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # File handler with rotation
        if log_to_file:
            file_handler = RotatingFileHandler(
                log_file_path,
                maxBytes=log_max_bytes,
                backupCount=log_backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, log_level.upper()))
            file_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance for a specific module.
        
        Args:
            name: Name of the module (usually __name__)
            
        Returns:
            logging.Logger: Logger instance
            
        Example:
            from utils.logger import AgentLogger
            logger = AgentLogger.get_logger(__name__)
            logger.info("Starting service...")
        """
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
        return cls._loggers[name]


def setup_logger(log_level: str = "INFO",
                 log_to_file: bool = True,
                 log_file_path: str = "./data/logs/agent.log",
                 log_max_bytes: int = 10485760,
                 log_backup_count: int = 5,
                 log_colored: bool = True) -> logging.Logger:
    """
    Convenience function to setup and get the main logger.
    
    Args:
        log_level: Logging level
        log_to_file: Whether to log to file
        log_file_path: Path to log file
        log_max_bytes: Maximum size before rotation
        log_backup_count: Number of backup files
        log_colored: Use colored output
        
    Returns:
        logging.Logger: Main logger instance
    """
    AgentLogger.setup(
        log_level=log_level,
        log_to_file=log_to_file,
        log_file_path=log_file_path,
        log_max_bytes=log_max_bytes,
        log_backup_count=log_backup_count,
        log_colored=log_colored
    )
    return AgentLogger.get_logger("crypto_agent")


def get_logger(name: str = "crypto_agent") -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually module name)
        
    Returns:
        logging.Logger: Logger instance
    """
    return AgentLogger.get_logger(name)


# Example usage
if __name__ == "__main__":
    # Setup logger
    logger = setup_logger(log_level="DEBUG", log_colored=True)
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test module-specific logger
    module_logger = get_logger("test_module")
    module_logger.info("Module-specific log message")
    
    print("\n✅ Logger test completed! Check ./data/logs/agent.log for file output.")
