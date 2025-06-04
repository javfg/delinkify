import tempfile

from loguru import logger
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, InlineQueryHandler

from delinkify.config import config
from delinkify.handler import HandlerError
from delinkify.router import Router


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not isinstance(update, Update) or not update.inline_query:
        return

    logger.error(f'Request "{update.inline_query.query}" caused error "{context.error}"')

    await context.bot.send_message(
        chat_id=config.dump_group_id, text=f'Error in request: {update.inline_query.query}\n{context.error}'
    )


class DelinkifyBot:
    def __init__(self, token: str, router: Router):
        self.app = Application.builder().read_timeout(60).write_timeout(60).token(token).build()
        self.router = router
        self.app.add_handler(CommandHandler('dl', self.dl))
        self.app.add_handler(InlineQueryHandler(self.inline_dl))
        self.app.add_error_handler(error_handler)

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
    logger.info('Starting Video Downloader Bot')

    router = Router()
    bot = DelinkifyBot(config.token, router)

    bot.run()
