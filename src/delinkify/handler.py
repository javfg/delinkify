import os
from collections.abc import Callable
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse
from uuid import uuid4

from loguru import logger
from telegram import (
    InlineQueryResultPhoto,
    InlineQueryResultVideo,
    InputMedia,
    InputMediaPhoto,
    InputMediaVideo,
)
from telegram.ext import ContextTypes

DUMP_CHANNEL_ID = os.getenv('DUMP_CHANNEL_ID')


class DelinkedMedia:
    def __init__(
        self,
        files: list[Path | str] | None = None,
        caption=None,
    ):
        self.files = files or []
        self.caption = caption

    def get_suffix(self, f: Path | str) -> str:
        match f:
            case Path():
                return f.suffix
            case str():
                return f'.{urlparse(f).path.split(".")[-1]}'

    def as_input_media(self) -> list[InputMedia]:
        ims = []
        for f in self.files:
            match self.get_suffix(f):
                case '.jpg':
                    ims.append(InputMediaPhoto(media=f))
                case '.mp4':
                    ims.append(InputMediaVideo(media=f, caption=None))
        return ims

    async def as_inline_query_results(
        self, context: ContextTypes.DEFAULT_TYPE
    ) -> list[InlineQueryResultPhoto | InlineQueryResultVideo]:
        rs = []
        for f in self.files:
            match self.get_suffix(f):
                case '.jpg':
                    logger.debug(f'sending video {f} to dump')
                    m = await context.bot.send_photo(DUMP_CHANNEL_ID, f)
                    p = InlineQueryResultPhoto(
                        id=uuid4(),
                        photo_url=m.photo[0].file_id,
                        title=self.caption[:140],
                        thumbnail_url=m.photo[0].file_id,
                        caption=self.caption,
                    )
                    rs.append(p)
                case '.mp4':
                    logger.debug(f'sending video {f} to dump')
                    m = await context.bot.send_video(DUMP_CHANNEL_ID, f)
                    v = InlineQueryResultVideo(
                        id=uuid4(),
                        video_url=m.video.file_id,
                        mime_type='video/mp4',
                        title=self.caption[:140],
                        thumbnail_url=m.video.thumbnail.file_id,
                        caption=self.caption,
                    )
                    rs.append(v)
        return rs

    def to_inline_query_results(
        self, context: ContextTypes.DEFAULT_TYPE
    ) -> list[InlineQueryResultPhoto | InlineQueryResultVideo]:
        results = []

        for m in self.media:
            if isinstance(m, InputMediaPhoto):
                results.append(self.build_query_result_photo(m))
            elif isinstance(m, InputMediaVideo):
                results.append(self.build_query_result_video(m))

        return results


class Handler(Protocol):
    async def handle(self) -> DelinkedMedia: ...


class HandlerError(Exception):
    pass


def handle_like(pattern: str | None = None) -> Callable[[type], type]:
    def decorator(cls):
        cls._url_pattern = pattern
        return cls

    return decorator
