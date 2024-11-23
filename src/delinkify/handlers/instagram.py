import re
from pathlib import Path

from instaloader import Instaloader, Post
from loguru import logger

from delinkify.handler import DelinkedMedia, HandlerError, handle_like
from delinkify.handlers.default import DefaultHandler


@handle_like(r'^https://www.instagram.com/(?:p|reel)/')
class InstagramHandler:
    def __init__(self, url: str) -> None:
        self.name = 'instagram-multi'
        self.url = url

    async def handle(self, temp_dir: str) -> DelinkedMedia:
        shortcode_re = r'https://www.instagram.com/(?:p|reel)/(?P<shortcode>[^/\n?]+)/?.*'

        m = re.match(shortcode_re, self.url)
        if not m:
            raise HandlerError(f'invalid instagram url {self.url}')

        shortcode = m.groupdict().get('shortcode')
        if not shortcode:
            raise HandlerError(f'invalid instagram url {self.url}')

        i = Instaloader(quiet=True, dirname_pattern=f'{temp_dir}')

        post = Post.from_shortcode(i.context, shortcode)

        # if the post is a just a video, we can use the default handler
        if post.is_video:
            logger.info(f'post {shortcode} is a video, deferring to default handler')
            return await DefaultHandler(self.url).handle()
        else:
            i.download_post(post, temp_dir)
            fs = [f for f in Path(temp_dir).glob('*') if f.suffix.lower() in ['.jpg', '.mp4']]
            fs.sort()
            caption = 'an instagram post'
            caption_file = Path(temp_dir).glob('*.txt')
            if f := next(caption_file, None):
                caption = Path(f).read_bytes().decode('utf-8')[:1024]

            logger.info(f'post {shortcode} contains {len(fs)-2} media in it')
            return DelinkedMedia(files=fs[:6], caption=caption)
