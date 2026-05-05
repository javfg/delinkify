from telegram.ext import Application, CallbackContext, ExtBot
from yt_dlp.utils.jslib.devalue import TYPE_CHECKING

from delinkify.config import Config
from delinkify.handler.router import Router

if TYPE_CHECKING:
    from delinkify.util.cache import Cache


class DelinkifyContext(CallbackContext[ExtBot, dict, dict, dict]):
    def __init__(
        self,
        application: Application,
        chat_id: int | None = None,
        user_id: int | None = None,
    ) -> None:
        super().__init__(application=application, chat_id=chat_id, user_id=user_id)
        self.config: Config = application.bot_data['config']
        self.router: Router = application.bot_data['router']
        self.cache: Cache = application.bot_data['cache']
