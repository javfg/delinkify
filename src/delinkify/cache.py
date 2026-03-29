import atexit
import json
import sys
import threading
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from loguru import logger

from delinkify.config import config
from delinkify.context import DelinkifyContext
from delinkify.media import Media


@dataclass
class CacheEntry:
    file_id: str
    caption: str | None
    mime_type: str

    @classmethod
    def from_json(cls, data: dict) -> CacheEntry:
        return cls(**{f.name: data[f.name] for f in fields(cls)})


class Cache:
    def __init__(self):
        self._cache: dict[str, list[CacheEntry]] = self._load()
        self._save_interval = config.cache_save_interval
        self._modified = False
        self._timer: threading.Timer = None
        self._periodic_save()
        atexit.register(self._shutdown)

    def _load(self) -> dict[str, list[CacheEntry]]:
        try:
            with open(config.cache_path) as f:
                c = json.load(f)
                cache_size = sys.getsizeof(c)
                logger.info(f'loaded cache with {len(c)} entries, consuming {cache_size} bytes')
                return {url: [CacheEntry(**entry) for entry in entries] for url, entries in c.items()}
        except FileNotFoundError, json.JSONDecodeError:
            logger.warning(f'cache file {config.cache_path} not found or invalid, starting with empty cache')
            return {}

    def _shutdown(self) -> None:
        logger.info('shutting down cache, saving to disk')
        if self._timer:
            self._timer.cancel()
        self._save()

    def _periodic_save(self) -> None:
        logger.info('running periodic cache save...')
        self._save()
        self._timer = threading.Timer(self._save_interval, self._periodic_save)
        self._timer.daemon = True
        self._timer.start()

    def _save(self) -> None:
        if not self._modified:
            logger.info('cache not modified, skipping save')
            return
        cache_path = Path(config.cache_path)
        if not cache_path.exists():
            cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config.cache_path, 'w') as f:
            json.dump({url: [asdict(e) for e in entries] for url, entries in self._cache.items()}, f)
            logger.info(f'saved cache with {len(self._cache)} entries, file size {f.tell()} bytes')
        self._modified = False

    def get(self, key, context: DelinkifyContext) -> bool:
        entries = self._cache.get(key)
        if entries:
            logger.info(f'cache hit for {key}')
            for entry in entries:
                context.media.append(
                    Media(
                        source=entry.file_id,
                        original_url=key,
                        caption=entry.caption,
                        mime_type=entry.mime_type,
                    )
                )
            return True
        else:
            logger.info(f'cache miss for {key}')
            return False

    def set(self, medias: list[Media]) -> None:
        self._cache[medias[0].original_url] = [
            CacheEntry(
                file_id=m.url,
                caption=m.caption,
                mime_type=m.mime_type,
            )
            for m in medias
        ]
        self._modified = True
        logger.info(f'added {len(medias)} entries to cache for {medias[0].original_url}')
