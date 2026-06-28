# Changelog

## 1.0.2
*Released on June 28, 2026*

* Install git in the docker image to allow uv to install dependencies from git
  repositories (`6ab541c`)


## 1.0.1
*Released on June 28, 2026*

* Update dependencies to latest versions (`d124a30`)
* Fixed dump messages failing html parsing because of errors containing `<` and
  `>` characters (`c9cc71b`)
* Be more lenient with formats in instagram single handler. Now it will fall back to
  `best` format if the other formats fail (`929f187`)


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
