import hashlib
import mimetypes
from pathlib import Path
from uuid import uuid4

from loguru import logger
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResult,
    InlineQueryResultArticle,
    InlineQueryResultCachedPhoto,
    InlineQueryResultCachedVideo,
    InputMediaPhoto,
    InputMediaVideo,
    InputTextMessageContent,
    LinkPreviewOptions,
)

from delinkify.context import DelinkifyContext
from delinkify.util.video import MAX_VIDEO_SIZE_MB, shrink


class MediaCollection:
    def __init__(
        self,
        url: str,
    ):
        self.url = url
        self.media: dict[str, Media] = {}
        self.media_dir = hashlib.sha256(self.url.encode()).hexdigest()[:32]

    def __len__(self) -> int:
        return len(self.media)

    def __str__(self) -> str:
        return f'media collection for {self.url}, is_materialized={self.is_materialized} media_count={len(self.media)}'

    def add_media(self, media: Media, context: DelinkifyContext) -> None:
        media.url = self.url
        self.media[media.result_id] = media
        context.cache.set(self.url, self)

    def get_media(self, result_id: str, context: DelinkifyContext) -> Media:
        m = self.media.get(result_id)
        if m is None:
            raise ValueError(f'media with result_id {result_id} not found')
        return m

    def get_media_path(self, context: DelinkifyContext) -> Path:
        return context.config.media_path / self.media_dir

    @property
    def is_materialized(self) -> bool:
        return all(m.is_materialized for m in self.media.values())

    def results(self, context: DelinkifyContext) -> list[InlineQueryResult]:
        return [media.as_result(context) for media in self.media.values()]

    def to_dict(self) -> dict:
        return {
            'url': self.url,
            'media': {result_id: m.to_dict() for result_id, m in self.media.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> MediaCollection:
        mc = cls(url=data['url'])
        mc.media = {result_id: Media.from_dict(m) for result_id, m in data['media'].items()}
        return mc


class Media:
    def __init__(
        self,
        source: Path,
        caption: str | None = None,
    ):
        self.source = Path(source)
        self.caption = caption or 'Some unknown media'
        self.file_id: str | None = None
        self.url: str | None = None
        self.result_id = uuid4().hex

    def __str__(self) -> str:
        return (
            f'media source={self.source} file_id={self.file_id} is_materialized={self.is_materialized} '
            f'result_id={self.result_id}'
        )

    @property
    def is_materialized(self) -> bool:
        return self.file_id is not None

    @property
    def mime_type(self) -> str:
        mime_type, _ = mimetypes.guess_type(self.source)
        if mime_type is None:
            raise ValueError(f'could not determine mimetype for {self.source}')
        return mime_type

    async def materialize(self, context: DelinkifyContext, inline_message_id: str) -> None:
        if self.mime_type.startswith('video/'):
            if self.source.stat().st_size > MAX_VIDEO_SIZE_MB * 1024 * 1024:
                new_source = Path(f'{self.source.with_suffix("")}-shrunk{self.source.suffix}')
                await shrink(self.source, new_source)
                self.source = new_source
            logger.debug(f'uploading video {self.source} with mime type {self.mime_type}')
            m = await context.bot.send_video(
                context.config.dump_chat_id,
                self.source,
                caption=self.url or self.caption[:1024],
                write_timeout=600,
            )
            if not m.video:
                raise ValueError('video upload failed')
            self.file_id = m.video.file_id
        elif self.mime_type.startswith('image/'):
            m = await context.bot.send_photo(
                context.config.dump_chat_id,
                self.source,
                caption=self.url or self.caption[:1024],
            )
            self.file_id = m.photo[-1].file_id
        else:
            raise ValueError(f'unsupported mimetype: {self.mime_type}')

    async def update_message(self, context: DelinkifyContext, inline_message_id: str) -> None:
        if self.file_id is None:
            raise ValueError('cannot update message with non-materialized media')
        if self.mime_type.startswith('video/'):
            media = InputMediaVideo(media=self.file_id, caption=self.caption[:1024])
        elif self.mime_type.startswith('image/'):
            media = InputMediaPhoto(media=self.file_id, caption=self.caption[:1024])
        else:
            raise ValueError(f'unsupported mimetype: {self.mime_type}')
        await context.bot.edit_message_media(
            media=media,
            inline_message_id=inline_message_id,
        )

    def as_result(self, context: DelinkifyContext) -> InlineQueryResult:
        if self.is_materialized:
            assert self.file_id is not None
            if self.mime_type.startswith('video/'):
                return InlineQueryResultCachedVideo(
                    id=self.result_id,
                    video_file_id=self.file_id,
                    title=self.caption[:140],
                    caption=self.caption[:1024],
                )
            if self.mime_type.startswith('image/'):
                return InlineQueryResultCachedPhoto(
                    id=self.result_id,
                    photo_file_id=self.file_id,
                    title=self.caption[:140],
                    caption=self.caption[:1024],
                )
            raise ValueError(f'unsupported mimetype: {self.mime_type}')
        else:
            return InlineQueryResultArticle(
                id=self.result_id,
                title=self.caption[:140],
                description='Some media that can be delinkified',
                input_message_content=InputTextMessageContent(
                    '⏳ Delinkifying!',
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                ),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('...', callback_data='noop')]]),
            )

    def to_dict(self) -> dict:
        return {
            'source': str(self.source),
            'caption': self.caption,
            'file_id': self.file_id,
            'url': self.url,
            'result_id': self.result_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Media:
        m = cls(
            source=Path(data['source']),
            caption=data['caption'],
        )
        m.file_id = data['file_id']
        m.url = data['url']
        m.result_id = data['result_id']
        return m
