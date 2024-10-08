import logging

class LoggerService:
    def __init__(self, name: str, log_file: str = None, level: int = logging.INFO) -> None:
        """
        Initializes the Logger class.

        :param name: The name of the logger.
        :param log_file: The file where logs should be saved. If None, logs will be output to the console.
        :param level: The logging level.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Create handlers
        if log_file:
            # File handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

    def get_logger(self) -> logging.Logger:
        """
        Returns the logger instance.
        
        :return: The configured logger.
        """
        return self.logger

    def info(self, message: str) -> None:
        """
        Logs an info message.
        
        :param message: The message to log.
        """
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """
        Logs a warning message.
        
        :param message: The message to log.
        """
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """
        Logs an error message.
        
        :param message: The message to log.
        """
        self.logger.error(message)

    def debug(self, message: str) -> None:
        """
        Logs a debug message.
        
        :param message: The message to log.
        """
        self.logger.debug(message)
