"""Test bout-en-bout du worker.

Pré-requis : le worker doit tourner (`docker compose up -d worker`).
Ce test simule ce que fera Gradio :
    1. Crée un batch en DB (état 'queued')
    2. Push un job dans Redis
    3. Poll la DB toutes les 2s jusqu'à voir 'completed' ou 'failed'

Usage :
    docker compose exec worker python -m scripts.test_worker

Note : avec INFERENCE_BACKEND=mock c'est instantané. Avec comfyui, compte ~3 min/image.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time

from src.common.logging import configure_logging
from src.common.models import BatchRequest
from src.db import close_pool, init_pool, repository
from src.worker import enqueue_batch

POLL_INTERVAL = 2.0
TIMEOUT = 1500.0  # 25 min, large pour couvrir 4 images CPU


async def main() -> int:
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))
    await init_pool()

    try:
        # 1. Création du batch
        request = BatchRequest(
            subject="test bout-en-bout du worker",
            style="anime",
            ambiance="douce",
            cadrage="carre",
            image_count=2,
        )
        batch_id = await repository.create_batch(request)
        print(f"\n✅ Batch créé : {batch_id}")

        # 2. Push dans la queue
        await enqueue_batch(batch_id)
        print(f"✅ Job poussé dans la queue Redis")
        print(f"   En attente du worker (polling toutes les {POLL_INTERVAL}s)...\n")

        # 3. Polling de l'état
        start = time.time()
        last_state = "queued"
        while time.time() - start < TIMEOUT:
            batch = await repository.get_batch(batch_id)
            if batch is None:
                print("❌ Batch disparu de la DB")
                return 1

            if batch.state != last_state:
                elapsed = time.time() - start
                print(f"   [{elapsed:6.1f}s] État : {last_state} → {batch.state}")
                last_state = batch.state

            if batch.state == "completed":
                images = await repository.get_images_for_batch(batch_id)
                print(f"\n✅ Batch terminé en {time.time() - start:.1f}s")
                print(f"   {len(images)} images générées :")
                for img in images:
                    print(f"     - seed={img.seed}, file={img.file_path}")
                return 0

            if batch.state == "failed":
                print(f"\n❌ Batch en erreur : {batch.error_message}")
                return 1

            await asyncio.sleep(POLL_INTERVAL)

        print(f"\n❌ Timeout après {TIMEOUT}s, dernier état : {last_state}")
        return 1

    finally:
        await close_pool()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))