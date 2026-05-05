import json

from delinkify.context import DelinkifyContext
from delinkify.handler import Handler
from delinkify.media import Media, MediaCollection
from delinkify.util import gdl


class RedditURL(Handler):
    """Handler for delinkifying Reddit posts using URLs."""

    url_patterns = [
        r'^https://(www\.|old\.|new\.|m\.)?reddit\.com/r/[\w-]+/comments/\w+(/[\w%-]*)?/?$',
        r'^https://(www\.|old\.|new\.|m\.)?reddit\.com/gallery/\w+',
    ]
    weight = 1000

    async def handle(self, url: str, context: DelinkifyContext) -> MediaCollection:
        mc = MediaCollection(url=url)
        media_path = mc.get_media_path(context)
        job = gdl(url, media_path)
        job.run()

        caption = None
        meta_file = media_path / 'metadata.json'
        if meta_file.exists():
            meta = json.loads(meta_file.read_text())
            caption = meta.get('description') or meta.get('title')

        for f in media_path.rglob('*'):
            if f.is_file() and f.suffix != '.json':
                mc.add_media(Media(source=f, caption=caption or f.name), context)

        return mc
