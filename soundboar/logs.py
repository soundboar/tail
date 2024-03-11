import logging
import os
from copy import deepcopy

from uvicorn.config import LOGGING_CONFIG

from soundboar import __title__

DEFAULT_LOG_FORMAT = "%(pathname)s:%(lineno)d | %(asctime)s | %(levelname)-8s | %(name).4s | %(message)s"
DEFAULT_LOG_CONFIG = deepcopy(LOGGING_CONFIG)
DEFAULT_LOG_CONFIG["formatters"]["default"]["fmt"] = DEFAULT_LOG_FORMAT
_LEVELS = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}


def setup(log_level: str = "NOTSET"):
    """Setup soundboars logger

    Usage:

        from soundboar.logs import setup, getLogger

        setup()
        logger = getLogger()
        logger.info('info message')
    """
    log_level = os.environ.setdefault("LOG_LEVEL", log_level)
    logging.getLogger().setLevel(log_level)
    # Copy the logging config from uvicorn to sqlalchemy and create a similar textada-logger
    logging_config = deepcopy(DEFAULT_LOG_CONFIG)
    logger_template = logging_config["loggers"]["uvicorn"]
    logger_template["level"] = log_level
    logging_config["loggers"] = {
        __title__: deepcopy(logger_template),
        "alembic": deepcopy(logger_template),
        "uvicorn": deepcopy(logger_template),
        "fastapi": deepcopy(logger_template),
        "urllib3": deepcopy(logger_template),
    }
    logging.config.dictConfig(logging_config)
    return logging_config


def getLogger(name: str = __title__):  # noqa
    return logging.getLogger(name)


get_logger = getLogger
logger = get_logger()
