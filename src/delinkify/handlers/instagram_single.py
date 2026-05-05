from pathlib import Path
from typing import Any

from loguru import logger
from yt_dlp import YoutubeDL

from delinkify.context import DelinkifyContext
from delinkify.handler import Handler
from delinkify.media import Media, MediaCollection


class InstagramSingle(Handler):
    """Handler for delinkifying Instagram post with a single video.

    All reels are a single video, and some posts which will arrive here after
    the InstagramPost handler yields them (when that one is implemented, if ever).
    """

    url_patterns = [
        r'^https://(www.)?instagram.com/(share/)?reel/([\w-]+)',
        r'^https://(www.)?instagram.com/p/([\w-]+)',
    ]
    weight = 500

    ydl_params: dict[str, Any] = {
        'allow_multiple_audio_streams': True,
        'outtmpl': None,
        'quiet': True,
        'noprogress': True,
        'noplaylist': True,
        'logger': logger,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0',
        },
        'format': (
            'bestvideo[vcodec^=avc][filesize_approx<35M]+bestaudio/'
            'best[vcodec^=avc][filesize_approx<35M]/'
            'best[filesize_approx<35M]'
        ),
        'merge_output_format': 'mp4',
    }

    async def handle(self, url: str, context: DelinkifyContext) -> MediaCollection:
        mc = MediaCollection(url=url)
        media_path = mc.get_media_path(context)
        self.ydl_params['outtmpl'] = f'{media_path}/%(id)s.%(ext)s'

        with YoutubeDL(params=self.ydl_params) as ydl:
            video_info = ydl.extract_info(url, download=True)

        source = Path(ydl.prepare_filename(video_info))

        if 'requested_formats' in video_info:
            vcodec = next(
                (f.get('vcodec') for f in video_info['requested_formats'] if f.get('vcodec')),
                'unknown',
            )
            format_id = '+'.join(f['format_id'] for f in video_info['requested_formats'])
        else:
            vcodec = video_info.get('vcodec', 'unknown')
            format_id = video_info.get('format_id', 'unknown')

        logger.info(f'size: {source.stat().st_size} bytes, codec: {vcodec}, format: {format_id}')

        mc.add_media(
            Media(
                source=source,
                caption=video_info.get('title'),
            ),
            context,
        )

        return mc
