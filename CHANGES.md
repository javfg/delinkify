# Changelog

## 1.0.0
*Released on May 5, 2026*

* First major revision. Complete rewrite of the bot. Now all handlers download the
  media files and send them to the dump group lazily by using `chosen_inline_result`
  events. This gives the bot infinite time to prepare the videos and to upload them,
  as Telegram has heavily nerfed the upload speed and it was impossible to finish
  uploads before the inline query timeout.

* Updated to python 3.14
* Updated to python-telegram-bot 22.7
* Switched to using `uv`, `ruff` and `ty`
* Added a url cache, so that media is never downloaded/uploaded twice.
