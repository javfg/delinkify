import os

from gallery_dl.job import DataJob

from delinkify.context import DelinkifyContext
from delinkify.handler import Handler, HandlerError
from delinkify.media import Media
from delinkify.util import clean_url


class TwitterURL(Handler):
    """Handler for delinkifying Twitter posts using URLs."""

    url_patterns = [
        r'^https://(www.)?x.com/[\w]+/status/(\d+)',
        r'^https://(www.)?twitter.com/[\w]+/status/(\d+)',
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

        if len(job.data[0]) == 2 and job.data[0][0] == 2:
            caption = job.data[0][1].get('content', 'Downloaded media')

        for item in job.data[1:]:
            if len(item) == 3:
                if item[2].get('type') == 'video':
                    await context.add_media(
                        Media(
                            source=item[1],
                            caption=f'{clean_url(url)}\n{caption}'[:1024],
                            mime_type=item[2].get('mime_type'),
                        )
                    )
                elif item[2].get('type') == 'photo':
                    await context.add_media(
                        Media(
                            source=item[1].split('?', 1)[0] + '.jpg',
                            caption=f'{clean_url(url)}\n{caption}'[:1024],
                            mime_type=item[2].get('mime_type'),
                            height=item[2].get('height', 768),
                            width=item[2].get('width', 1024),
                        )
                    )
