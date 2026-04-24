"""
Helper pour pousser des jobs dans la queue arq depuis n'importe où.
Utilisé par Gradio (au moment de la soumission) et par les scripts de test.
"""

from __future__ import annotations

from uuid import UUID

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from src.common.config import get_settings
from src.common.logging import get_logger

log = get_logger(__name__)


async def get_queue() -> ArqRedis:
    """Retourne une connexion ArqRedis pour pousser des jobs."""
    settings = get_settings()
    return await create_pool(
        RedisSettings(host=settings.redis_host, port=settings.redis_port)
    )


async def enqueue_batch(batch_id: UUID) -> None:
    """Pousse un job `generate_batch(batch_id)` dans la queue."""
    queue = await get_queue()
    try:
        await queue.enqueue_job("generate_batch", str(batch_id))
        log.info("queue.enqueued", batch_id=str(batch_id))
    finally:
        await queue.close()