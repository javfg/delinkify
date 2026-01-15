import re
from pathlib import Path

from instaloader import Instaloader, Post
from loguru import logger

from delinkify.config import config
from delinkify.context import DelinkifyContext
from delinkify.handler import Handler, HandlerError
from delinkify.media import Media


class InstagramMulti(Handler):
    """Handler for delinkifying Instagram posts with multiple media items."""

    url_patterns = [
        r'^https://(www.)?instagram.com/p/(?P<shortcode>[\w-]+)/?.*',
    ]
    weight = -1

    async def handle(self, url: str, context: DelinkifyContext) -> None:
        m = re.match(self.url_patterns[0], url)
        if not m:
            raise HandlerError(f'invalid instagram url {url}')
        shortcode = m.groupdict().get('shortcode')
        if not shortcode:
            raise HandlerError(f'invalid instagram url {url}')

        tmpdir = config.tmp_dir
        i = Instaloader(quiet=True, dirname_pattern=f'{tmpdir}')
        post = Post.from_shortcode(i.context, shortcode)

        if post.is_video:
            raise HandlerError(f'post {shortcode} is a single video, yielding')
        else:
            i.download_post(post, tmpdir)
            fs = [f for f in Path(tmpdir).glob('*') if f.suffix.lower() in ['.jpg', '.mp4']]
            fs.sort()
            caption = None
            caption_file = Path(tmpdir).glob('*.txt')
            if f := next(caption_file, None):
                caption = f.read_bytes().decode('utf-8')

            logger.info(f'post {shortcode} contains {len(fs) - 2} media in it')
            for f in fs:
                await context.add_media(
                    Media(
                        source=f,
                        caption=caption,
                        original_url=url,
                    )
                )
