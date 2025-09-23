# Sorted after the PEP8 standard
# https://www.python.org/dev/peps/pep-0008/
#
import os
import sys
from datetime import datetime
import logging as legacy_logging
from typing import TextIO, Union


class Logging(object):
    """
    This class is a wrapper for the logging module.
    It will create a handler for both console and file output, while setting the log level for both.
    Log level "info" for the console and "debug" for the log file, respectively.

    ***All default logging functions are available.***

    :Example:

    main.py:
    >>> from modules.loggingBase import Logging
    >>> Logging().basicConfig(console_log_level='debug')
    >>> logger = Logging().getLogger()
    >>> logger.info("This will show up in the console and in the log file")
    >>> logger.debug("This will also show up in the console and in the log file")
    >>> Logging().set_console_log_level('info')
    >>> logger.debug("This will no longer show up in the console, but will still be in the log file")
    [2024-08-12 13:56:16,863 - main.py->main():11] - INFO: This is an info message, from main
    """

    __all__ = ['debug', 'error', 'fatal', 'info', 'warn', 'warning', 'critical', 'exception',
               'basicConfig', 'getLogger', 'set_console_log_level']

    # Custom data type for the log level
    class LogLevel:
        # The log level can be set to a string or an int
        # If it is set to a string it will be converted to an int
        def __init__(self, logLevel: Union[int, str]):
            if (isinstance(logLevel, str)):
                # Check if the log level is a valid textual log level
                if (logLevel.upper() in legacy_logging._nameToLevel.keys()):
                    numeric_level = getattr(
                        legacy_logging, logLevel.upper(), None)
                    self.logLevel = numeric_level
                else:
                    raise ValueError(
                        'Invalid textual log level: %s' % logLevel)
            elif (isinstance(logLevel, int)):
                # Check if the log level is a valid numeric log level
                if (logLevel in legacy_logging._nameToLevel.values()):
                    self.logLevel = logLevel
                else:
                    raise ValueError(
                        'Invalid numeric log level: %s' % logLevel)
            else:
                raise ValueError('Invalid log level: %s' % logLevel)

        def __str__(self):
            return legacy_logging._levelToName[self.logLevel]

        def __repr__(self):
            return str(self.logLevel)

        def __int__(self):
            return self.logLevel

    # Singleton instance
    _instance = None

    # Private variables
    __logging = None
    __logfile_handler = None
    __console_handler = None

    # Import all log levels from the legacy_logging module so it is accessable from the logger object
    # Example: logger.INFO
    for level in legacy_logging._nameToLevel.keys():
        # Create a variable for each log level
        exec(f"{level} = legacy_logging._nameToLevel['{level}']")

    # Import all logging functions from the legacy_logging module so it is accessable from the logger object
    # Example: logger.debug("This is a test")
    for function in [key.lower() for key in legacy_logging._nameToLevel.keys()]:
        # Create a function for each logging function that is also available outside this if statement
        exec(f"def {function}(self, message: str, *args, **kwargs) -> None:\n\tself.log(self.{function.upper()}, message, *args, **kwargs)")

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logging, cls).__new__(cls)
            cls.basicConfig(cls._instance)
        return cls._instance

    def basicConfig(self,
                    console_log_output: TextIO = sys.stdout,
                    console_log_level: str = legacy_logging.getLevelName(
                        (legacy_logging.INFO)),
                    logfiles_path: str = './logs/',
                    logfile_name: str = f'data-{(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))}.log',
                    logfile_log_level: str = legacy_logging.getLevelName(
                        (legacy_logging.DEBUG)),
                    log_line_template: str = "[%(asctime)s - %(filename)s->%(funcName)s():%(lineno)s] - %(levelname)s: %(message)s") -> None:
        """
            Method to configure the logger.

            :param console_log_output: The output for the console handler, default is sys.stdout
            :param console_log_level: The log level for the console handler, default is logging.INFO
            :param logfiles_path: The path to the log files, default is './logs/'
            :param logfile_name: The name of the log file, default is 'data-{(datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))}.log'
            :param logfile_log_level: The log level for the log file handler, default is logging.DEBUG
            :param log_line_template: The template for the log line, default is "[%(asctime)s - %(filename)s->%(funcName)s():%(lineno)s] - %(levelname)s: %(message)s""

            :type console_log_output: TextIO
            :type console_log_level: str
            :type logfiles_path: str
            :type logfile_name: str
            :type logfile_log_level: str
            :type log_line_template: str

            :return: None
            :rtype: None
        """

        # Create logger
        self.__logging = legacy_logging.getLogger(__name__)
        # Set global log level to 'debug' (required for handler levels to work)
        self.__logging.setLevel(legacy_logging.DEBUG)

        # This guarantees that only one handler is created for the console
        if self.__console_handler is not None:
            self.__logging.removeHandler(self.__console_handler)

        # Create console handler
        self.__console_handler = legacy_logging.StreamHandler(
            console_log_output)
        self.__console_handler.setLevel(int(self.LogLevel(console_log_level)))
        # Create and set formatter, add console handler to logger
        self.__console_handler.setFormatter(
            legacy_logging.Formatter(log_line_template))
        self.__logging.addHandler(self.__console_handler)

        # This guarantees that only one handler is created for the log file
        if self.__logfile_handler is not None:
            self.__logging.removeHandler(self.__logfile_handler)

        # Create file handler
        self.__logfile_handler = legacy_logging.FileHandler(
            logfiles_path + logfile_name)
        self.__logfile_handler.setLevel(int(self.LogLevel(logfile_log_level)))
        # Create and set formatter, add log file handler to logger
        self.__logfile_handler.setFormatter(
            legacy_logging.Formatter(log_line_template))
        self.__logging.addHandler(self.__logfile_handler)

        # Check if logfiles_path exists and create it if not
        if (not os.path.exists("./" + logfiles_path)):
            os.mkdir(logfiles_path)

    def getLogger(self) -> legacy_logging.Logger:
        """
        Method to get the logger object.

        :return: The logger object
        :rtype: legacy_logging.Logger
        """
        return self.__logging

    # Function to change the console log level on the fly
    def set_console_log_level(self, log_level: int):
        """
        Method to change the console log level on the fly.

        :param log_level: The log level for the console handler

        :type log_level: int

        :return: None
        :rtype: None
        """
        self.__console_handler.setLevel(log_level)
