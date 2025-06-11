import os

from gallery_dl.job import DataJob

from delinkify.context import DelinkifyContext
from delinkify.handler import Handler, HandlerError
from delinkify.media import Media
from delinkify.util import clean_url


class RedditURL(Handler):
    """Handler for delinkifying Reddit posts using URLs."""

    url_patterns = [
        r'^https://(www.|old.)?reddit.com/r/[\w-]+/comments/[\w-]+/[\w-]+/?',
        r'^https://(www.|old.)?reddit.com/gallery/[\w-]+/?',
    ]
    weight = 1000

    async def handle(self, url: str, context: DelinkifyContext) -> None:
        # shut gallery-dl up
        with open(os.devnull, 'w') as devnull:
            job = DataJob(url)
            job.file = devnull
            job.run()

        if not job.data:
            raise HandlerError(f'no data found for {url}')

        caption = job.data[0][1].get('title', 'Downloaded media')

        for item in job.data[1:]:
            if len(item) == 3:
                if item[2].get('is_video', True):
                    await context.add_media(
                        Media(
                            source=item[2].get('media', {}).get('reddit_video', {}).get('fallback_url'),
                            caption=f'{clean_url(url)}\n{caption}'[:1024],
                        )
                    )
                else:
                    file_name = item[1].rsplit('/', 1)[-1].split('.', 1)[0]
                    dimensions = item[2].get('media_metadata', {}).get(file_name, {}).get('o', [{}][0])
                    await context.add_media(
                        Media(
                            source=item[1],
                            caption=f'{clean_url(url)}\n{caption}'[:1024],
                            height=dimensions.get('y', 768),
                            width=dimensions.get('x', 1024),
                        )
                    )
