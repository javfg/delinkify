import inspect
import re
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from loguru import logger

from delinkify.handler import Handler


class Router:
    def __init__(self) -> None:
        self.handlers: list[Handler] = []
        self.load_handlers()

    def register_handler(self, handler: type[Handler]) -> None:
        h = handler()
        w = h.weight if h.weight >= 0 else 'disabled'
        self.handlers.append(h)
        logger.info(f'registered handler {h.name} with weight {w} for urls like {handler.url_patterns}')

    def is_handler(self, obj: Any, module: Any) -> bool:
        return inspect.isclass(obj) and issubclass(obj, Handler) and obj.__module__ == module.__name__

    def is_valid_url(self, url: str) -> bool:
        result = urlparse(url)
        return all([result.netloc, result.path])

    def load_handlers(self) -> None:
        handler_dir = Path(__file__).parent / 'handlers'
        for handler_path in handler_dir.glob('[!__]*.py'):
            spec = spec_from_file_location(handler_path.stem, handler_path)
            if not spec or not spec.loader:
                raise ImportError(f'could not load handler {handler_path}')
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
            for _, obj in inspect.getmembers(module):
                if self.is_handler(obj, module):
                    self.register_handler(obj)

    def get_handlers(self, url: str) -> list[Handler]:
        valid_handlers: list[Handler] = []
        if not self.is_valid_url(url):
            logger.warning(f'invalid url: {url}')
            return []
        enabled_handlers = [h for h in self.handlers if h.weight >= 0]
        for h in enabled_handlers:
            for p in h.url_patterns:
                if re.match(p, url):
                    valid_handlers.append(h)
                    break
        valid_handlers = sorted(valid_handlers, key=lambda h: h.weight, reverse=True)
        logger.trace(f'handlers for {url}: {[h.name for h in valid_handlers]}')
        return valid_handlers
