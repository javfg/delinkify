import os
from urllib.parse import urlparse
from uuid import uuid4

from loguru import logger
from telegram import InlineQueryResultVideo, Update
from telegram.ext import Application, ContextTypes, InlineQueryHandler
from yt_dlp import YoutubeDL


class VideoDownloaderBot:
    def __init__(self, token: str):
        self.app = Application.builder().token(token).build()
        self.app.add_handler(InlineQueryHandler(self.inline_query))
        self.ydl_params = {'format': 'best[ext=mp4]/best', 'quiet': True, 'no_warnings': True}

    def is_valid_url(self, url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def get_video_info(self, source: str) -> tuple[str, str, str] | None:
        try:
            with YoutubeDL(params=self.ydl_params) as ydl:
                info = ydl.extract_info(source, download=False)
                return (
                    info.get('url'),
                    info.get('thumbnail', 'https://i.sstatic.net/PtbGQ.png'),
                    info.get('title', 'Downloaded video'),
                )
        except Exception as e:
            logger.error(f'Error getting video info: {e}')
            return None

    async def inline_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.inline_query.query
        logger.info(f'Received inline query: {query}')

        if not query or not self.is_valid_url(query):
            logger.info(f'Invalid URL {query}')
            return await update.inline_query.answer([])

        video_url, thumbnail_url, title = self.get_video_info(query)
        if not video_url:
            return await update.inline_query.answer([])

        result = [
            InlineQueryResultVideo(
                id=str(uuid4()),
                video_url=video_url,
                mime_type='video/mp4',
                thumbnail_url=thumbnail_url,
                title=title,
                caption=title,
            )
        ]
        await update.inline_query.answer(result)

    def run(self):
        self.app.run_polling()


def main():
    logger.info('Starting Video Downloader Bot')
    bot_token = os.getenv('BOT_TOKEN')
    bot = VideoDownloaderBot(bot_token)
    bot.run()
