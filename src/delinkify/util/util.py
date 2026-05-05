from pathlib import Path

import gallery_dl
from gallery_dl.job import DownloadJob
from loguru import logger

from delinkify.context import DelinkifyContext


def get_cookie_file_path(handler: str, context: DelinkifyContext) -> str | None:
    """Get the path to the cookie file if it exists."""

    cookie_path = context.config.cookie_path / f'{handler}.txt'
    if cookie_path.exists():
        logger.debug(f'got cookie from {cookie_path}')
        return str(cookie_path)
    return None


def gdl(
    url: str,
    media_path: Path,
    cookie_file_path: str | None = None,
) -> DownloadJob:
    gallery_dl.config.set(('extractor',), 'base-directory', str(media_path))
    gallery_dl.config.set(('extractor', 'reddit'), 'directory', [])
    gallery_dl.config.set(('extractor', 'reddit'), 'filename', '{id}_{num:>02}.{extension}')
    gallery_dl.config.set(
        ('extractor',),
        'postprocessors',
        [
            {
                'name': 'metadata',
                'event': 'post',
                'mode': 'json',
            }
        ],
    )
    if cookie_file_path:
        gallery_dl.config.set(('extractor', 'reddit'), 'cookies', cookie_file_path)

    return DownloadJob(url)
