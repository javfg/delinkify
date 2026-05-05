import inspect
import logging
import os
import sys
from dataclasses import dataclass, fields
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger


def must_str(env_var: str) -> str:
    value = os.environ.get(env_var)
    if value is None:
        raise ValueError(f'missing required environment variable {env_var}')
    return value


def path_or_default(env_var: str, default: str) -> Path:
    root_path = Path(__file__).parent.parent.parent
    value = os.environ.get(env_var)
    if value is None:
        return (root_path / default).absolute()
    return Path(value).absolute()


def prepare_path(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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


@dataclass
class Config:
    bot_token: str
    dump_chat_id: str
    errors_chat_id: str
    log_level: str
    log_path: Path
    cache_save_interval: int
    cache_path: Path
    media_path: Path
    cookie_path: Path

    @classmethod
    def from_env(cls) -> Config:
        env_loaded = load_dotenv()
        if env_loaded:
            logger.info('config .env file loaded successfully')
        else:
            logger.warning('config .env file not found')

        log_level = os.environ.get('DELINKIFY_LOG_LEVEL', 'INFO')
        log_path = path_or_default('DELINKIFY_LOG_PATH', 'logs')

        logger.remove()
        logger.add(sink=sys.stderr, level=log_level)
        logger.add(
            sink=log_path / f'{datetime.now().strftime("%Y-%m-%d")}.log',
            level=log_level,
            rotation='6 months',
            compression='zip',
        )
        logging.basicConfig(handlers=[InterceptHandler()], level=logging.WARNING, force=True)

        self = cls(
            bot_token=must_str('DELINKIFY_BOT_TOKEN'),
            dump_chat_id=must_str('DELINKIFY_DUMP_CHAT_ID'),
            errors_chat_id=os.environ.get('DELINKIFY_ERRORS_CHAT_ID', must_str('DELINKIFY_DUMP_CHAT_ID')),
            log_level=log_level,
            log_path=log_path,
            cache_save_interval=int(os.environ.get('DELINKIFY_CACHE_SAVE_INTERVAL', '300')),
            cache_path=path_or_default('DELINKIFY_CACHE_PATH', 'cache'),
            media_path=path_or_default('DELINKIFY_MEDIA_PATH', 'media'),
            cookie_path=path_or_default('DELINKIFY_COOKIE_PATH', 'cookies'),
        )

        prepare_path(self.log_path)
        prepare_path(self.cache_path)
        prepare_path(self.media_path)
        prepare_path(self.cookie_path)

        logger.info('config parsed successfully')
        for f in [fi for fi in fields(self) if fi.name not in ['bot_token', 'extra']]:
            logger.info(f'{f.name:<{20}}: {getattr(self, f.name)}')

        return self
