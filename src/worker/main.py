"""Stub worker : log au démarrage et boucle sans rien consommer.

Sprint 2 remplacera ce stub par un vrai worker arq qui dépile Redis.
"""

from __future__ import annotations

import asyncio
import signal

from src.common.config import get_settings
from src.common.logging import configure_logging, get_logger

settings = get_settings()
configure_logging(settings.log_level)
log = get_logger(__name__)

_shutdown = asyncio.Event()


def _handle_signal(signum: int, _frame: object) -> None:
    log.info("worker.signal.received", signal=signum)
    _shutdown.set()


async def main() -> None:
    log.info(
        "worker.starting",
        backend=settings.inference_backend,
        redis=settings.redis_url,
        postgres=f"{settings.postgres_host}:{settings.postgres_port}",
        comfyui=settings.comfyui_url,
    )

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    # Heartbeat en attendant le vrai code arq du sprint 2
    while not _shutdown.is_set():
        log.debug("worker.heartbeat")
        try:
            await asyncio.wait_for(_shutdown.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            continue

    log.info("worker.stopped")


if __name__ == "__main__":
    asyncio.run(main())