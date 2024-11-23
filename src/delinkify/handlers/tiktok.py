import re
from pathlib import Path
from uuid import uuid4

from loguru import logger
from yt_dlp import YoutubeDL

from delinkify.handler import DelinkedMedia, HandlerError, handle_like


@handle_like(r'^https://(www|vm).tiktok.com/')
class TiktokHandler:
    def __init__(self, url: str) -> None:
        self.name = 'tiktok'
        self.url = url
        self.ydl_params = {
            'format': 'best[ext=mp4][filesize<10M]/best[filesize<10M]',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'max_filesize': 10 * 1024 * 1024,
        }

    async def handle(self, temp_dir: str) -> DelinkedMedia:
        shortcode_res = [
            r'https://vm.tiktok.com/(?P<shortcode>[^/\n?]+)/?.*',
            r'https://www.tiktok.com/@[^/]+/video/(?P<shortcode>[^/\n?]+)/?.*',
        ]

        m = None
        for shortcode_re in shortcode_res:
            m = re.match(shortcode_re, self.url)
            if m:
                break
        if not m:
            raise HandlerError(f'invalid tiktok url {self.url}')

        shortcode = m.groupdict().get('shortcode')
        if not shortcode:
            raise HandlerError(f'invalid tiktok url {self.url}')

        logger.info(f'tiktok shortcode: {shortcode}')

        with YoutubeDL(
            params={
                **self.ydl_params,
                'outtmpl': str(Path(temp_dir) / f'{uuid4()}.%(ext)s'),
            }
        ) as ydl:
            info = ydl.extract_info(self.url)
            if not info.get('requested_downloads'):
                raise HandlerError(f'no video found in {self.url}, perhaps it is too big?')

            files = [info['requested_downloads'][0]['filepath']]
            caption = info['title']

        return DelinkedMedia(files=files, caption=caption)
