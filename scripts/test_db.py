"""Test isolé du repository DB.

Usage :
    docker compose exec worker python -m scripts.test_db

Crée un batch, simule une génération, vérifie que tout est bien persisté.
Nettoie le batch créé à la fin pour ne pas polluer.
"""

from __future__ import annotations

import asyncio
import os

from src.common.logging import configure_logging, get_logger
from src.common.models import BatchRequest, GeneratedImage
from src.db import close_pool, init_pool, repository

log = get_logger(__name__)


async def main() -> None:
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))
    await init_pool()

    try:
        # 1. Création d'un batch
        request = BatchRequest(
            subject="test du repository",
            style="anime",
            ambiance="douce",
            cadrage="carre",
            image_count=2,
        )
        batch_id = await repository.create_batch(request)
        print(f"\n✅ Batch créé : {batch_id}")

        # 2. Lecture immédiate (état queued)
        batch = await repository.get_batch(batch_id)
        print(f"   État après create : {batch.state if batch else 'NOT FOUND'}")
        assert batch is not None and batch.state == "queued"

        # 3. Marque comme processing
        await repository.mark_processing(
            batch_id,
            prompt_enriched="high quality, anime style, soft lighting, test du repository",
            negative_prompt="lowres, blurry",
        )
        batch = await repository.get_batch(batch_id)
        print(f"   État après mark_processing : {batch.state if batch else 'NOT FOUND'}")
        assert batch is not None and batch.state == "processing"
        assert batch.prompt_enriched is not None
        assert batch.started_at is not None

        # 4. Ajout de 2 images
        for seed in (1000, 1001):
            generated = GeneratedImage(
                seed=seed,
                file_path=f"test/{seed}.png",
                width=512,
                height=512,
            )
            image_id = await repository.add_image(batch_id, generated)
            print(f"   Image ajoutée : seed={seed}, id={image_id}")

        # 5. Lecture des images
        images = await repository.get_images_for_batch(batch_id)
        print(f"   Images récupérées : {len(images)}")
        assert len(images) == 2

        # 6. Marque comme completed
        await repository.mark_completed(batch_id)
        batch = await repository.get_batch(batch_id)
        print(f"   État final : {batch.state if batch else 'NOT FOUND'}")
        assert batch is not None and batch.state == "completed"
        assert batch.completed_at is not None

        # 7. Listing récent
        recent = await repository.list_recent_batches(limit=5)
        print(f"\n   {len(recent)} batches récents trouvés")

        print("\n✅ Tous les tests passent")

    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())