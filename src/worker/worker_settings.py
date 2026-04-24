"""
Configuration arq + lifecycle hooks.

arq découvre cette classe `WorkerSettings` au démarrage. Elle déclare :
- les fonctions exécutables (`functions`)
- la connexion Redis (`redis_settings`)
- les hooks startup/shutdown qui initialisent/ferment les ressources partagées
  (pool DB, backend d'inférence)

Ressources stockées dans `ctx` (dict passé à chaque job) :
- ctx["backend"] : instance d'InferenceBackend (Mock ou ComfyUI)
"""

from __future__ import annotations

from typing import Any

from arq.connections import RedisSettings

from src.common.config import get_settings
from src.common.logging import configure_logging, get_logger
from src.db import close_pool, init_pool
from src.inference import get_backend
from src.worker import translator
from src.worker.jobs import generate_batch

# Init logging au plus tôt
_settings = get_settings()
configure_logging(_settings.log_level)
log = get_logger(__name__)


# -----------------------------------------------------------------------------
# Hooks de lifecycle
# -----------------------------------------------------------------------------
async def startup(ctx: dict[str, Any]) -> None:
    """Appelé une fois au démarrage du worker."""
    log.info("worker.startup")
    await init_pool()
    ctx["backend"] = get_backend()
    translator.load()
    log.info("worker.startup.done", backend=type(ctx["backend"]).__name__)


async def shutdown(ctx: dict[str, Any]) -> None:
    """Appelé une fois à l'arrêt du worker (SIGTERM, SIGINT)."""
    log.info("worker.shutdown")
    await close_pool()
    log.info("worker.shutdown.done")


# -----------------------------------------------------------------------------
# Settings arq (découverte par convention)
# -----------------------------------------------------------------------------
class WorkerSettings:
    """Configuration arq, découverte automatiquement par `arq <module>.WorkerSettings`."""

    functions = [generate_batch]
    on_startup = startup
    on_shutdown = shutdown

    redis_settings = RedisSettings(
        host=_settings.redis_host,
        port=_settings.redis_port,
    )

    # Job timeout : il faut couvrir le cas le plus lent
    # ComfyUI CPU : ~3 min/image × 4 images = 12 min, on prend 20 min de marge
    job_timeout = 1200  # 20 min

    # Concurrence : 1 job à la fois suffit (CPU saturé par ComfyUI de toute façon)
    max_jobs = 1

    # Pas de retry automatique : on gère les erreurs en marquant le batch en DB
    max_tries = 1