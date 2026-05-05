from pathlib import Path
from typing import Any

from loguru import logger
from yt_dlp import YoutubeDL

from delinkify.context import DelinkifyContext
from delinkify.handler import Handler
from delinkify.media import Media, MediaCollection


class RedditVideo(Handler):
    """Handler for delinkifying Reddit Video posts."""

    url_patterns = [
        r'^https://v.redd.it/[\w-]+/?',
    ]
    weight = 500

    ydl_params: dict[str, Any] = {
        'format': 'bv[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b',
        # 'format': 'bestvideo[ext=mp4][filesize_approx<35M]+bestaudio',
        'max_filesize': 35 * 1024 * 1024,
        'allow_multiple_audio_streams': True,
        'merge_output_format': 'mp4',
        'outtmpl': None,
        'quiet': True,
        'noprogress': True,
        'noplaylist': True,
        'logger': logger,
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
