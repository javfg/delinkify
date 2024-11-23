import inspect
import os
import re
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from loguru import logger

from delinkify.handler import Handler


class Router:
    def __init__(self) -> None:
        self.handlers: list[type] = []
        self.default_handler = None
        self.load_handlers()

    def register_handler(self, handler: type) -> None:
        if handler._url_pattern:
            self.handlers.append(handler)
            logger.info(f'{handler.__name__} registered for urls like {handler._url_pattern}')
        else:
            self.default_handler = handler
            logger.info(f'{handler.__name__} registered as default handler')

    def is_handler(self, obj: Any) -> bool:
        return inspect.isclass(obj) and hasattr(obj, '_url_pattern')

    def load_handlers(self) -> dict[str, type]:
        handler_dir = Path(os.path.abspath(__file__)).parent / 'handlers'
        for handler_path in handler_dir.glob('[!__]*.py'):
            spec = spec_from_file_location(handler_path.stem, handler_path)
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
            for _, obj in inspect.getmembers(module):
                if self.is_handler(obj):
                    self.register_handler(obj)

    def is_valid_url(self, url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.netloc, result.path])  # we need at least a domain and a path
        except ValueError:
            return False

    def get_handler(self, url: str) -> Handler | None:
        if not self.is_valid_url(url):
            logger.trace(f'invalid url {url}')
            return
        for handler in self.handlers:
            m = re.match(handler._url_pattern, url)
            if m:
                logger.info(f'handler {handler.__name__} matches url {url}')
                return handler(url)
        logger.info(f'no handler found for {url}')
        return self.default_handler(url)
