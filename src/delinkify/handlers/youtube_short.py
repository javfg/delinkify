from pathlib import Path
from typing import Any

from loguru import logger
from yt_dlp import YoutubeDL

from delinkify.context import DelinkifyContext
from delinkify.handler import Handler
from delinkify.media import Media, MediaCollection


class YoutubeShortURL(Handler):
    """Handler for delinkifying YouTube shorts."""

    url_patterns = [
        r'^https://(www.)?youtube.com/shorts/([\w-]+)',
    ]
    weight = 1000

    ydl_params: dict[str, Any] = {
        'format': 'best[ext=mp4]',
        'allow_multiple_audio_streams': True,
        'outtmpl': None,
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

    async def handle(self, url: str, context: DelinkifyContext) -> MediaCollection:
        mc = MediaCollection(url=url)
        media_path = mc.get_media_path(context)
        self.ydl_params['outtmpl'] = f'{media_path}/%(id)s.%(ext)s'

        with YoutubeDL(params=self.ydl_params) as ydl:
            video_info = ydl.extract_info(url, download=True)

        source = Path(ydl.prepare_filename(video_info))
        logger.info(f'downloaded video size: {source.stat().st_size} bytes')

        mc.add_media(
            Media(
                source=source,
                caption=video_info.get('description') or video_info.get('title') or source.name,
            ),
            context,
        )

        return mc
