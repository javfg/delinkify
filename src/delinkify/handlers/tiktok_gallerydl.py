import mimetypes
import os
import tempfile
from pathlib import Path

import gallery_dl
from gallery_dl.job import DownloadJob
from loguru import logger

from delinkify.context import DelinkifyContext
from delinkify.handler import Handler
from delinkify.media import Media
from delinkify.util import get_cookie_file_path


class TiktokGalleryDL(Handler):
    """Handler for delinkifying TikTok posts using gallery-dl."""

    url_patterns = [
        r'^https://(www.|vm.)?tiktok.com/[\w-]+',
        r'^https://(www.|vm.)?tiktok.com/@[\w-]+/video/\d+',
    ]
    weight = 500

    gallery_dl.config.load({
        'extractor': {
            'tiktok': {
                'cookies': str(get_cookie_file_path('tiktok')),
                'directory': '',
            }
        }
    })

    async def handle(self, url: str, context: DelinkifyContext) -> None:
        with tempfile.TemporaryDirectory(delete=False) as tmpdir:
            gallery_dl.config.set(('extractor',), 'base-directory', tmpdir)

            job = DownloadJob(url)
            job.run()

            for f in os.listdir(tmpdir):
                logger.info(f'downloaded file: {f}')
                mime_type = mimetypes.guess_type(f)[0] or 'video/mp4'

                await context.add_media(
                    Media(
                        source=Path(tmpdir) / f,
                        caption=f,
                        original_url=url,
                        mime_type=mime_type,
                    )
                )
