from pathlib import Path

from loguru import logger
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update

from delinkify.config import config
from delinkify.context import DelinkifyContext


async def error_handler(update: object, context: DelinkifyContext) -> None:
    """Logs error and report in the dump group."""
    if not isinstance(update, Update) or not update.inline_query:
        return
    error_text = '\n\n'.join(str(e) for e in context.errors)
    logger.error(f'all handlers failed for {update.inline_query.query}: {error_text}')
    await context.bot.send_message(
        chat_id=config.dump_group_id,
        text=f'all handlers failed for: {update.inline_query.query}\n\n{error_text}',
        disable_web_page_preview=True,
    )
    await update.inline_query.answer(
        results=[
            InlineQueryResultArticle(
                id='error',
                title='Error processing your request',
                input_message_content=InputTextMessageContent(
                    'The spectacle resists delinkification. The machine fights '
                    'for its survival. Try with another video.'
                ),
            )
        ],
        cache_time=0,
    )


async def send_unhandled_link(update: Update) -> None:
    """Sends a message to the user if no handler is found."""
    if not update.inline_query or not (url := update.inline_query.query):
        return
    await update.inline_query.answer(
        results=[
            InlineQueryResultArticle(
                id='no_handlers',
                title='Unable to delinkify that',
                input_message_content=InputTextMessageContent(
                    f'I cannot delinkify {url}, check it out manually if you are '
                    'OK with feeding the capitalist machine, you monster!'
                ),
            )
        ],
        cache_time=0,
    )


def clean_url(url: str) -> str:
    """Clean a URL by removing query parameters and fragments."""
    cleaned_url = url.split('?', 1)[0].split('#', 1)[0]
    return cleaned_url.strip('/')


def get_cookie_file_path(handler: str) -> str | None:
    """Get the path to the cookie file if it exists."""

    cookie_path = Path(__file__).parent.parent.parent / 'cookies' / f'{handler}.txt'
    if cookie_path.exists():
        return str(cookie_path)
    return None
