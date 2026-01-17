from pathlib import Path
from typing import Any

from loguru import logger
from yt_dlp import YoutubeDL

from delinkify.config import config
from delinkify.context import DelinkifyContext
from delinkify.handler import Handler
from delinkify.media import Media
from delinkify.util import get_cookie_file_path


class TiktokYTDLP(Handler):
    """Handler for delinkifying TikTok posts using yt-dlp."""

    url_patterns = [
        r'^https://(www.|vm.)?tiktok.com/[\w-]+',
        r'^https://(www.|vm.)?tiktok.com/@[\w-]+/video/\d+',
    ]
    weight = 1000

    ydl_params: dict[str, Any] = {
        'format': 'best[ext=mp4][filesize<10M]/best[filesize<10M]',
        'allow_multiple_audio_streams': True,
        'outtmpl': f'{config.tmp_dir}/%(id)s.%(ext)s',
        'quiet': True,
        'noprogress': True,
        'noplaylist': True,
        'logger': logger,
        'max_filesize': 10 * 1024 * 1024,  # 10MiB
        'cookiefile': get_cookie_file_path('tiktok'),
    }

    async def handle(self, url: str, context: DelinkifyContext) -> None:
        with YoutubeDL(params=self.ydl_params) as ydl:
            video_info = ydl.extract_info(url, download=True)

        source = Path(ydl.prepare_filename(video_info))
        logger.info(f'video size: {source.stat().st_size} bytes')

        await context.add_media(
            Media(
                source=source,
                caption=video_info.get('title'),
                original_url=url,
            )
        )
