import os
import tempfile

from loguru import logger
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, InlineQueryHandler

from delinkify.handler import HandlerError
from delinkify.logging import setup_logging
from delinkify.router import Router


class DelinkifyBot:
    def __init__(self, token: str, router: Router):
        self.app = Application.builder().read_timeout(60).write_timeout(60).token(token).build()
        self.router = router
        self.app.add_handler(CommandHandler('dl', self.dl))
        self.app.add_handler(InlineQueryHandler(self.inline_dl))

    async def dl(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args or update.edited_message:
            return  # we do not care about messages without args or edited messages
        url = context.args[0]
        logger.debug(f'Received /dl command with args: {context.args}')

        handler = self.router.get_handler(url)
        dm = None
        if handler:
            prefix = getattr(handler, 'name', 'unknown') + '-'
            with tempfile.TemporaryDirectory(dir='.', prefix=prefix) as temp_dir:
                try:
                    dm = await handler.handle(temp_dir)
                except HandlerError as e:
                    logger.error(e)
                await update.message.reply_media_group(media=dm.as_input_media(), caption=dm.caption)

    async def inline_dl(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        url = update.inline_query.query
        if not url:
            return
        logger.debug(f'Received inline query: {url}')

        handler = self.router.get_handler(url)
        dm = None
        if handler:
            prefix = getattr(handler, 'name', 'unknown') + '-'
            with tempfile.TemporaryDirectory(prefix=prefix, delete=False) as temp_dir:
                try:
                    dm = await handler.handle(temp_dir)
                except HandlerError as e:
                    logger.error(e)
                await update.inline_query.answer(results=await dm.as_inline_query_results(context), cache_time=60)

    def run(self):
        self.app.run_polling()


def main():
    bot_token = os.getenv('BOT_TOKEN')
    log_level = os.getenv('LOG_LEVEL', 'INFO')

    setup_logging(log_level)
    logger.info('Starting Video Downloader Bot')

    router = Router()
    bot = DelinkifyBot(bot_token, router)

    bot.run()
