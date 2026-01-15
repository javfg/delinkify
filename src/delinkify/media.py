import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from loguru import logger
from telegram import (
    Bot,
    InlineQueryResult,
    InlineQueryResultPhoto,
    InlineQueryResultVideo,
    InputMediaPhoto,
    InputMediaVideo,
)

from delinkify.config import config
from delinkify.util import clean_url


class Media:
    def __init__(
        self,
        source: Path | str,
        caption: str | None = None,
        original_url: str | None = None,
        mime_type: str | None = None,
        height: int | None = None,
        width: int | None = None,
    ):
        self.source = source
        self.caption = caption or 'Some unknown media'
        self.original_url = clean_url(original_url) if original_url else None
        self.mime_type = mime_type or self._determine_mime_type(source)
        self.height = height
        self.width = width
        self.url: str
        self.thumbnail_url: str
        if isinstance(source, str):
            self.url = source
            self.thumbnail_url = source

    def _determine_mime_type(self, source: str | Path) -> str:
        mime_type: str | None = None
        match source:
            case str():
                mime_type, _ = mimetypes.guess_type(urlparse(source).path)
            case Path():
                mime_type, _ = mimetypes.guess_type(source)
        if not mime_type:
            raise ValueError('could not determine mimetype')
        return mime_type

    async def materialize(self, bot: Bot) -> None:
        if isinstance(self.source, str):
            return
        if self.mime_type.startswith('image/'):
            m = await bot.send_photo(config.dump_group_id, self.source, caption=self.original_url)
            self.url = m.photo[0].file_id
            self.thumbnail_url = m.photo[0].file_id
        elif self.mime_type.startswith('video/'):
            m = await bot.send_video(config.dump_group_id, self.source, caption=self.original_url)
            if m.video:
                self.url = m.video.file_id
                if m.video.thumbnail:
                    self.thumbnail_url = m.video.thumbnail.file_id
            else:
                raise ValueError('video upload failed: no video in response')
        logger.trace(f'materialized media: {self.mime_type} {self.url}')

    def as_result(self) -> InlineQueryResult:
        if self.mime_type.startswith('image/'):
            return InlineQueryResultPhoto(
                id=str(uuid4()),
                photo_url=self.url,
                title=self.caption[:140] if self.caption else 'A photo',
                caption=self.caption[:1024],
                photo_width=self.width,
                photo_height=self.height,
                thumbnail_url=self.url,
            )
        elif self.mime_type.startswith('video/'):
            return InlineQueryResultVideo(
                id=str(uuid4()),
                video_url=self.url,
                title=self.caption[:140] if self.caption else 'A video',
                caption=self.caption[:1024],
                thumbnail_url=self.url,
                mime_type=self.mime_type,
            )
        raise ValueError(f'unsupported mimetype: {self.mime_type}')

    def as_media(self, include_caption: bool = True) -> InputMediaPhoto | InputMediaVideo:
        caption = self.caption if include_caption else None
        if self.mime_type.startswith('image/'):
            return InputMediaPhoto(media=self.url, caption=caption)
        elif self.mime_type.startswith('video/'):
            return InputMediaVideo(media=self.url, caption=caption)
        raise ValueError(f'unsupported mimetype for media: {self.mime_type}')
