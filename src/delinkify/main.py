from loguru import logger
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, InlineQueryHandler

from delinkify.config import config
from delinkify.handler import DelinkifyContext, HandlerError
from delinkify.router import Router
from delinkify.util import error_handler, send_unhandled_link


class DelinkifyBot:
    def __init__(self, token: str):
        ct = ContextTypes(context=DelinkifyContext)
        self.app = Application.builder().read_timeout(60).write_timeout(60).context_types(ct).token(token).build()
        self.app.add_handler(CommandHandler('dl', self.dl))
        self.app.add_handler(InlineQueryHandler(self.inline_dl))
        self.app.add_error_handler(error_handler)
        self.router = Router()

    async def handle_query(self, update: Update, context: DelinkifyContext) -> None:
        if update.inline_query and update.inline_query.query:  # inline query
            url = update.inline_query.query.strip()
        elif context.args:  # direct command
            url = context.args[0]
        else:
            return
        logger.debug(f'received query: {url}')
        if not (handlers := self.router.get_handlers(url)):
            await send_unhandled_link(update)
            return
        for handler in handlers:
            logger.trace(f'trying handler {handler.name} for {url}')
            try:
                await handler.handle(url, context)
                if context.media:
                    logger.debug(f'obtained {len(context.media)} results')
                    break
                else:
                    logger.debug(f'handler {handler.name} did not return results')
            except Exception as e:
                context.errors.append(HandlerError(f'handler {handler.name} failed: {e}'))

    async def inline_dl(self, update: Update, context: DelinkifyContext) -> None:
        await self.handle_query(update, context)
        logger.trace(f'inline query results: {context.media}, errors: {context.errors}')
        if context.media:
            await update.inline_query.answer(  # type: ignore[union-attr]
                results=[media.as_result() for media in context.media],
                cache_time=60,
            )
        elif context.errors:
            await error_handler(update, context)

    async def dl(self, update: Update, context: DelinkifyContext) -> None:
        logger.debug(f'received dl command with args: {context.args}')
        await self.handle_query(update, context)
        if context.media and update.message:
            await update.message.reply_media_group([
                media.as_media(include_caption=(i == 0)) for i, media in enumerate(context.media)
            ])

    def run(self):
        self.app.run_polling()


def main():
    logger.info('Starting Delinkify Bot...')
    bot = DelinkifyBot(config.token)
    bot.run()
