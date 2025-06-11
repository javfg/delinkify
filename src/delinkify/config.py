import inspect
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger


def must_str(env_var: str) -> str:
    value = os.environ.get(env_var)
    if value is None:
        raise ValueError(f'missing required environment variable {env_var}')
    return value


def must_path(env_var: str) -> Path:
    return Path(must_str(env_var)).absolute()


def prepare_tmp_dir() -> Path:
    tmp_dir = Path('/tmp/delinkify')  # noqa: S108
    os.makedirs(tmp_dir, exist_ok=True)
    return tmp_dir


class InterceptHandler(logging.Handler):
    """Logging handler that intercepts logs and sends them to Loguru's logger."""

    def emit(self, record: logging.LogRecord) -> None:
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


class Config:
    """Configuration class for the Delinkify Bot."""

    def __init__(self):
        logger.debug('loading config')
        load_dotenv()

        self.token = must_str('DELINKIFY_TOKEN')
        self.dump_group_id = must_str('DELINKIFY_DUMP_GROUP_ID')
        log_path = must_path('DELINKIFY_LOG_PATH')
        log_level = os.environ.get('DELINKIFY_LOG_LEVEL', 'INFO')
        self.tmp_dir = prepare_tmp_dir()

        logger.remove()
        logger.add(sink=sys.stderr, level=log_level)
        logger.add(
            sink=log_path / f'{datetime.now().strftime("%Y-%m-%d")}.log',
            level=log_level,
            rotation='6 months',
            compression='zip',
        )


config = Config()
