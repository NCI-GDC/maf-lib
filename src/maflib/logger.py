"""Module for custom logging in maflib"""

import logging
import sys


class Logger(object):
    """Provides methods to obtain loggers."""

    # NB: do not use an empty string here!
    RootLogger = logging.getLogger("maflib")
    LoggerFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    @classmethod
    def setup_root_logger(cls):
        """Sets up the root logger for maflib.  This should only be called
        once
        """
        for handle in Logger.RootLogger.handlers:
            Logger.RootLogger.removeHandler(handle)
            Logger.RootLogger.setLevel(level=Logger.LoggerLevel)
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(Logger.LoggerFormat)
        handler.setFormatter(formatter)
        Logger.RootLogger.addHandler(handler)

    LoggerLevel = logging.INFO

    @classmethod
    def get_logger(cls, name, stream=None):
        """Gets a logger with the given name.  If a ``stream`` is not
        provided, the logger will be a child of the root logger, otherwise, a
        new logger is created using the given ``stream``."""
        if not stream:
            logger = Logger.RootLogger.getChild(name)
        else:
            logger = logging.getLogger(name)
            handler = logging.StreamHandler(stream)
            formatter = logging.Formatter(Logger.LoggerFormat)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

Logger.setup_root_logger()
