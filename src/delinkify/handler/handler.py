import traceback
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from loguru import logger
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.error import NetworkError

if TYPE_CHECKING:
    from delinkify.context import DelinkifyContext
    from delinkify.media.media import MediaCollection


class Handler(ABC):
    url_patterns: list[str]
    weight: int = 0

    @abstractmethod
    async def handle(self, url: str, context: DelinkifyContext) -> MediaCollection: ...

    @property
    def name(self) -> str:
        return self.__class__.__name__


class HandlerError(Exception):
    pass


async def inline_dl(update: Update, context: DelinkifyContext) -> None:
    if update.inline_query is None:
        return
    url = update.inline_query.query.strip()
    if not url.startswith('https://'):
        return
    logger.debug(f'received query: {url}')

    mc = context.cache.get_by_url(url)
    if mc is None:
        handlers = context.router.get_handlers(url)
        if not handlers:
            await reply_unable(update, context, url)
            return
        for handler in handlers:
            logger.trace(f'trying handler {handler.name} for {url}')
            try:
                mc = await handler.handle(url, context)
            except Exception as e:
                raise HandlerError(f'handler {handler.name} failed: {e}')
            if len(mc):
                logger.debug(f'obtained {len(mc)} media')
                break
            logger.debug(f'handler {handler.name} did not return media')
        else:
            logger.warning(f'all handlers failed to delinkify {url}')
            await reply_unable(update, context, url)
            return

    context.cache.set(url, mc)
    await update.inline_query.answer(results=mc.results(context))


async def chosen_inline(update, context: DelinkifyContext):
    result_id = update.chosen_inline_result.result_id
    inline_message_id = update.chosen_inline_result.inline_message_id

    if inline_message_id is None:
        logger.info('chosen inline result has no inline_message_id, assuming server/client-cached results')
        return  # we assume server-cached materialized result, telegram handled it

    m = context.cache.get_by_result_id(result_id)
    if m is None:
        raise HandlerError(f'no media for {result_id} in cache')

    if not m.is_materialized:
        logger.debug(f'materializing media for result_id {result_id}')
        try:
            await m.materialize(context, inline_message_id)
            context.cache.mark_modified()
        except Exception as e:
            raise HandlerError(f'materialization failed: {e}')

    logger.debug(f'updating message {inline_message_id}')
    await m.update_message(context, inline_message_id)


def _replace_html_entities(src: str | Exception) -> str:
    if isinstance(src, Exception):
        text = str(src)
    else:
        text = src
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    return text.replace('>', '&gt;')


async def error_handler(update: object, context: DelinkifyContext) -> None:
    if context.error is None:
        logger.error('error handler called without an error')
        return

    if isinstance(context.error, NetworkError):
        logger.warning(f'network error: {context.error}')
        return

    logger.opt(exception=context.error).error('exception while handling an update')

    chat_id_errors = context.config.errors_chat_id
    if not chat_id_errors:
        return

    tb = ''.join(traceback.format_exception(None, context.error, context.error.__traceback__))

    if isinstance(update, Update):
        user = update.effective_user
        chat = update.effective_chat
        user_info = f'user: {user.full_name} (@{user.username}, id: {user.id})' if user else 'user: N/A'

        if chat:
            chat_info = f'chat: {chat.title or chat.type} (id: {chat.id})'
        elif update.inline_query:
            chat_info = f'chat: inline query ("{update.inline_query.query}")'
        else:
            chat_info = 'chat: N/A'
    else:
        user_info = 'user: N/A'
        chat_info = 'chat: N/A'

    message = (
        f'⚠️ <b>an error occurred</b>\n\n'
        f'{user_info}\n'
        f'{chat_info}\n\n'
        f'<b>error:</b> {type(context.error).__name__}: {_replace_html_entities(context.error)}\n\n'
        f'<b>traceback:</b>\n<pre>{_replace_html_entities(tb)}'
    )
    message = message[:4000] + '</pre>'

    logger.debug(f'sending error message to chat {chat_id_errors}: \n\n{message}\n\n')

    await context.bot.send_message(
        chat_id=chat_id_errors,
        text=message,
        parse_mode='HTML',
        disable_web_page_preview=True,
    )


async def reply_unable(update: Update, context: DelinkifyContext, url: str) -> None:
    if update.inline_query is None:
        return
    await update.inline_query.answer(
        results=[
            InlineQueryResultArticle(
                id='error',
                title='Unable to delinkify that',
                input_message_content=InputTextMessageContent(
                    f'I could not delinkify {url}, check it out manually if you are '
                    'OK with feeding the capitalist machine, you monster!'
                ),
            )
        ],
        cache_time=0,
    )
