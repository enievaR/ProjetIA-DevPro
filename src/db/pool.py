"""Pool de connexions asyncpg, partagé dans toute l'app.

Init paresseuse : le pool est créé à la première utilisation, dans la boucle
asyncio courante. C'est nécessaire avec Gradio qui gère lui-même sa propre
event loop — initialiser le pool avant `launch()` créerait un pool attaché
à une boucle qui sera fermée juste après.

Le worker arq peut aussi utiliser `init_pool()` explicitement dans son hook
`on_startup` (où l'event loop existe déjà), mais l'init paresseuse marche
dans les deux cas.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg

from src.common.config import get_settings
from src.common.logging import get_logger

log = get_logger(__name__)

_pool: asyncpg.Pool | None = None
_pool_lock: asyncio.Lock | None = None


def _get_lock() -> asyncio.Lock:
    """Lock créé paresseusement pour ne pas le lier à une boucle au import-time."""
    global _pool_lock
    if _pool_lock is None:
        _pool_lock = asyncio.Lock()
    return _pool_lock


async def init_pool(min_size: int = 2, max_size: int = 10) -> asyncpg.Pool:
    """Initialise le pool global. Idempotent (safe à appeler plusieurs fois)."""
    global _pool
    async with _get_lock():
        if _pool is not None:
            return _pool

        settings = get_settings()
        log.info("db.pool.init", min_size=min_size, max_size=max_size)
        _pool = await asyncpg.create_pool(
            dsn=settings.postgres_dsn,
            min_size=min_size,
            max_size=max_size,
        )
        log.info("db.pool.ready")
        return _pool


async def close_pool() -> None:
    """Ferme le pool. À appeler à l'arrêt propre du process."""
    global _pool
    if _pool is not None:
        log.info("db.pool.close")
        await _pool.close()
        _pool = None


@asynccontextmanager
async def acquire_connection() -> AsyncIterator[asyncpg.Connection]:
    """Context manager pour obtenir une connexion du pool.

    Initialise le pool si nécessaire (lazy init dans la boucle courante).
    """
    pool = _pool if _pool is not None else await init_pool()
    async with pool.acquire() as conn:
        yield conn


def get_pool() -> asyncpg.Pool:
    """Retourne le pool. Lève si non-initialisé.

    À utiliser uniquement quand on sait que le pool a déjà été init
    (ex. dans un test après un await init_pool()).
    """
    if _pool is None:
        raise RuntimeError("Pool DB non-initialisé. Appelle `init_pool()` ou utilise `acquire_connection()`.")
    return _pool