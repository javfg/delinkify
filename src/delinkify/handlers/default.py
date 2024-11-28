from urllib.parse import urlparse

from loguru import logger
from yt_dlp import YoutubeDL

from delinkify.handler import DelinkedMedia, HandlerError, handle_like


@handle_like()
class DefaultHandler:
    def __init__(self, url: str) -> None:
        self.name = 'default'
        self.url = url
        self.ydl_params = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }

    def get_good_url(self, video_info: dict) -> str | None:
        first_url = video_info.get('url')
        if str(urlparse(first_url).path).endswith('.mp4'):
            return first_url
        for f in video_info.get('formats', []):
            other_url = f.get('url')
            if str(urlparse(other_url).path).endswith('.mp4'):
                return other_url
        return None

    def get_video_info(self, source: str) -> tuple[str, str, str] | None:
        try:
            with YoutubeDL(params=self.ydl_params) as ydl:
                return ydl.extract_info(source, download=False)
        except Exception as e:
            logger.error(f'Error getting video info: {e}')
            return None

    async def handle(self, _: str) -> DelinkedMedia:
        logger.info(f'default handler {self.url}')

        video_info = self.get_video_info(self.url)
        video_caption = video_info.get('title', 'Downloaded video')
        video_url = self.get_good_url(video_info)
        if not video_url:
            raise HandlerError(f'no video found in {self.url}')

        parsed_url = urlparse(self.url)
        short_url = f'{parsed_url.scheme}://{parsed_url.netloc}/{parsed_url.path}'

        logger.info(f'found video {video_url} in {self.url}')
        return DelinkedMedia(files=[video_url], caption=f'{short_url}\n{video_caption}'[:1024])
