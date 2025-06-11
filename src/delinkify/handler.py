from abc import ABC, abstractmethod

from delinkify.context import DelinkifyContext


class Handler(ABC):
    url_patterns: list[str]
    weight: int = 0

    @abstractmethod
    async def handle(self, url: str, context: DelinkifyContext): ...

    @property
    def name(self) -> str:
        return self.__class__.__name__


class HandlerError(Exception):
    pass
