import gallery_dl
from gallery_dl.job import DownloadJob

from delinkify.context import DelinkifyContext
from delinkify.handler import Handler
from delinkify.media import Media, MediaCollection


class TwitterURL(Handler):
    """Handler for delinkifying Twitter posts using URLs."""

    url_patterns = [
        r'^https://(www.)?x.com/[\w]+/status/(\d+)',
        r'^https://(www.)?twitter.com/[\w]+/status/(\d+)',
    ]
    weight = 1000

    gallery_dl.config.set(('extractor', 'twitter'), 'directory', [])

    async def handle(self, url: str, context: DelinkifyContext) -> MediaCollection:
        mc = MediaCollection(url=url)
        media_path = mc.get_media_path(context)
        gallery_dl.config.set(('extractor',), 'base-directory', str(media_path))

        job = DownloadJob(url)
        job.run()

        for f in media_path.rglob('*'):
            if f.is_file():
                m = Media(source=f, caption=f.name)
                mc.add_media(m, context)

        return mc
