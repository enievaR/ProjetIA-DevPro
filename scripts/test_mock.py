"""Test isolé du MockBackend.

Usage :
    docker compose exec worker python -m scripts.test_mock

Génère 3 images placeholder dans /data/images/ et affiche le chemin.
Pas besoin de Postgres/Redis/ComfyUI pour ce test.
"""

from __future__ import annotations

import asyncio
import os

from src.common.logging import configure_logging
from src.common.models import PromptSpec
from src.inference.mock import MockBackend


async def main() -> None:
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))
    backend = MockBackend(output_dir="/data/images")

    print(f"Health : {await backend.health()}")

    spec = PromptSpec(
        prompt="portrait of a young woman, red hair, forest background, sunset lighting",
        negative_prompt="lowres, blurry, deformed",
        width=512,
        height=512,
        seed_start=100,
    )

    print(f"\nGénération de 3 images placeholder...")
    images = await backend.generate(spec, count=3)

    print(f"\nRésultat :")
    for img in images:
        print(f"  - seed={img.seed}, file={img.file_path}, size={img.width}x{img.height}")


if __name__ == "__main__":
    asyncio.run(main())