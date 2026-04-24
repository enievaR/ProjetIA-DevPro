"""Script de test isolé pour ComfyUIBackend.

Usage (depuis le container worker) :
    docker compose exec worker python -m scripts.test_comfyui

Génère 1 image avec un prompt en dur, l'écrit dans /data/images, log le résultat.
Utile pour valider la chaîne d'inférence sans passer par worker/queue/DB.
"""

from __future__ import annotations

import asyncio
import sys

from src.common.logging import configure_logging, get_logger
from src.common.models import PromptSpec
from src.inference.comfyui import ComfyUIBackend
import os

log_level = os.getenv("LOG_LEVEL",'INFO')
log = get_logger(__name__)


async def main() -> int:
    backend = ComfyUIBackend(
        workflow_path="/app/workflows/sd15_txt2img.json",
        output_dir="/data/images",
    )

    # Vérification de l'état de ComfyUI
    log.info("test.health.check")
    if not await backend.health():
        log.error("test.health.fail", message="ComfyUI ne répond pas")
        return 1
    log.info("test.health.ok")

    # Spec de test
    random_seed = int.from_bytes(os.urandom(4), "big")

    spec = PromptSpec(
        prompt=(
            "A man walk in a city at night, all the lights are on, the city is alive"
            ", light are bright with a lot of colors"
        ),
        negative_prompt="lowres, blurry, deformed, bad anatomy, ugly, low quality",
        width=512,
        height=512,
        seed_start=random_seed,
    )

    log.info("test.generate.start", count=1)
    images = await backend.generate(spec, count=1)
    log.info("test.generate.done", images=[img.model_dump() for img in images])
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))