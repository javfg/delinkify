from pathlib import Path
from typing import Any

from loguru import logger
from yt_dlp import YoutubeDL

from delinkify.config import config
from delinkify.context import DelinkifyContext
from delinkify.handler import Handler
from delinkify.media import Media
from delinkify.util import clean_url


class YoutubeShortURL(Handler):
    """Handler for delinkifying YouTube shorts."""

    url_patterns = [
        r'^https://(www.)?youtube.com/shorts/([\w-]+)',
    ]
    weight = 1000

    ydl_params: dict[str, Any] = {
        'format': 'best[ext=mp4]',
        'allow_multiple_audio_streams': True,
        'outtmpl': f'{config.tmp_dir}/%(id)s.%(ext)s',
        'quiet': True,
        'noprogress': True,
        'noplaylist': True,
        'logger': logger,
        'extractor_args': {
            'youtube': {
                'player_client': ['web'],
            },
        },
    }

    async def handle(self, url: str, context: DelinkifyContext) -> None:
        with YoutubeDL(params=self.ydl_params) as ydl:
            video_info: dict[str, Any] = ydl.extract_info(url, download=True)  # type: ignore[attr-defined]
            video_caption = video_info.get('title', 'Downloaded video')

        source = Path(ydl.prepare_filename(video_info))
        logger.info(f'downloaded video size: {source.stat().st_size} bytes')

        await context.add_media(
            Media(
                source=source,
                caption=f'{clean_url(url)}\n{video_caption}'[:1024],
            )
        )
