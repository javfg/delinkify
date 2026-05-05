from __future__ import annotations

import atexit
import json
import threading
from pathlib import Path

from loguru import logger

from delinkify.media.media import Media, MediaCollection


class Cache:
    def __init__(self, path: Path, save_interval: int):
        self._path = path / 'cache.json'
        self._save_interval = save_interval
        self._by_result_id: dict[str, Media] = {}
        self._cache: dict[str, MediaCollection] = self._load()
        self._modified = False
        self._timer: threading.Timer | None = None

        self._schedule_save()
        atexit.register(self._shutdown)

    def __contains__(self, url: str) -> bool:
        return url in self._cache

    def set(self, url: str, mc: MediaCollection) -> None:
        logger.trace(f'setting cache for {url} with {len(mc)} media')
        self._cache[url] = mc
        for m in mc.media.values():
            self._by_result_id[m.result_id] = m
        self._modified = True

    def mark_modified(self) -> None:
        self._modified = True

    def get_by_url(self, url: str) -> MediaCollection | None:
        mc = self._cache.get(url)
        logger.trace(f'cache get by url {"HIT" if mc else "MISS"}: {mc or url}')
        return mc

    def get_by_result_id(self, result_id: str) -> Media | None:
        m = self._by_result_id.get(result_id)
        logger.trace(f'cache get by result_id {"HIT" if m else "MISS"}: {m or result_id}')
        return m

    def _load(self) -> dict[str, MediaCollection]:
        try:
            with self._path.open() as f:
                data = json.load(f)
        except FileNotFoundError, json.JSONDecodeError:
            logger.warning(f'cache {self._path} not found or invalid, starting empty')
            return {}

        cache = {url: MediaCollection.from_dict(mc_data) for url, mc_data in data.items()}
        for mc in cache.values():
            for m in mc.media.values():
                self._by_result_id[m.result_id] = m

        total = sum(len(mc) for mc in cache.values())
        logger.info(f'loaded cache: {total} media entries across {len(cache)} urls')
        return cache

    def _save(self) -> None:
        if not self._modified:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        serializable = {url: mc.to_dict() for url, mc in self._cache.items()}
        with self._path.open('w') as f:
            json.dump(serializable, f, indent=2)
        self._modified = False
        logger.info(f'saved cache: {len(self._cache)} entries')

    def _schedule_save(self) -> None:
        self._save()
        self._timer = threading.Timer(self._save_interval, self._schedule_save)
        self._timer.daemon = True
        self._timer.start()

    def _shutdown(self) -> None:
        logger.info('cache shutdown')
        if self._timer is not None:
            self._timer.cancel()
        self._save()
