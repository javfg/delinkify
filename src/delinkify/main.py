from importlib.metadata import version

from loguru import logger
from telegram.ext import Application, ChosenInlineResultHandler, ContextTypes, InlineQueryHandler

from delinkify.config import Config
from delinkify.context import DelinkifyContext
from delinkify.handler.handler import chosen_inline, error_handler, inline_dl
from delinkify.handler.router import Router
from delinkify.util.cache import Cache

config = Config.from_env()


class DelinkifyBot:
    def __init__(self):
        ct = ContextTypes(context=DelinkifyContext)
        self.app = (
            Application
            .builder()
            .pool_timeout(60)
            .read_timeout(60)
            .write_timeout(60)
            .context_types(ct)
            .token(config.bot_token)
            .build()
        )
        self.app.bot_data['config'] = config
        self.app.bot_data['router'] = Router()
        self.app.bot_data['pending']: list[str] = []  # list of result_ids that are pending materialization
        self.app.bot_data['cache'] = Cache(config.cache_path, config.cache_save_interval)
        self.app.add_error_handler(error_handler)
        self.app.add_handler(InlineQueryHandler(inline_dl))
        self.app.add_handler(ChosenInlineResultHandler(chosen_inline))

    def run(self):
        self.app.run_polling()


def main() -> None:
    ver = version('delinkify')
    logger.info(f'starting delinkify bot v{ver}...')
    bot = DelinkifyBot()
    bot.run()
