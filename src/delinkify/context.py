from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackContext, ExtBot

from delinkify.media import Media


class DelinkifyContext(CallbackContext[ExtBot, dict, dict, dict]):
    def __init__(
        self,
        application: Application,
        chat_id: int | None = None,
        user_id: int | None = None,
    ) -> None:
        super().__init__(application=application, chat_id=chat_id, user_id=user_id)
        self._media: list[Media] = []
        self._update: Update | None = None
        self.errors: list[Exception] = []

    @classmethod
    def from_update(cls, update: object, application: Application) -> DelinkifyContext:
        return super().from_update(update, application)

    @property
    def media(self) -> list[Media]:
        return self._media

    async def add_media(self, media: Media) -> None:
        await media.materialize(self.bot)
        self._media.append(media)

    @property
    def update(self) -> Update | None:
        return self._update

    @update.setter
    def update(self, value: Update | None) -> None:
        self._update = value
