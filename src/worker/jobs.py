"""Job arq : génère un batch d'images pour une requête utilisateur.

Pipeline :
1. Lit la requête en DB (état 'queued')
2. Construit le prompt enrichi via prompt_builder
3. Marque le batch en 'processing'
4. Appelle le backend d'inférence (Mock ou ComfyUI selon config)
5. Pour chaque image générée : insère en DB
6. Marque le batch 'completed' (ou 'failed' en cas d'erreur)

Cette fonction est appelée par arq (voir worker_settings.py).
Le `ctx` est un dict fourni par arq qui contient les ressources partagées
initialisées au startup (notamment le backend d'inférence).
"""

from __future__ import annotations

import random
from typing import Any
from uuid import UUID

from src.common.logging import get_logger
from src.common.models import BatchRequest
from src.db import repository
from src.inference import InferenceBackend
from src.prompt_builder import build
from src.worker import translator

log = get_logger(__name__)


async def generate_batch(ctx: dict[str, Any], batch_id_str: str) -> None:
    """Job arq : exécute la génération complète d'un batch.

    arq ne supporte pas nativement les UUID dans les arguments JSON, donc on
    sérialise en string et on parse.
    """
    batch_id = UUID(batch_id_str)
    backend: InferenceBackend = ctx["backend"]

    log.info("worker.batch.start", batch_id=str(batch_id))

    # 1. Récupère le batch créé par Gradio (en état 'queued')
    batch = await repository.get_batch(batch_id)
    if batch is None:
        log.error("worker.batch.not_found", batch_id=str(batch_id))
        return

    if batch.state != "queued":
        log.warning(
            "worker.batch.unexpected_state",
            batch_id=str(batch_id),
            state=batch.state,
        )
        return

    try:
        # 2. Traduit le sujet FR→EN puis reconstitue la BatchRequest
        subject_en = translator.translate(batch.subject)
        request = BatchRequest(
            subject=subject_en,
            style=batch.style,
            ambiance=batch.ambiance,
            cadrage=batch.cadrage,
            image_count=batch.image_count,
        )

        # 3. Construit le prompt enrichi (avec une seed aléatoire pour ce batch)
        seed_start = random.randint(1, 2_000_000_000)
        spec = build(request, seed_start=seed_start)

        # 4. Marque comme processing + persiste le prompt
        await repository.mark_processing(
            batch_id,
            prompt_enriched=spec.prompt,
            negative_prompt=spec.negative_prompt,
        )

        # 5. Génération
        log.info(
            "worker.inference.start",
            batch_id=str(batch_id),
            count=request.image_count,
            seed_start=seed_start,
        )
        images = await backend.generate(spec, count=request.image_count)
        log.info(
            "worker.inference.done",
            batch_id=str(batch_id),
            generated=len(images),
        )

        # 6. Persiste chaque image
        for img in images:
            await repository.add_image(batch_id, img)

        # 7. Marque terminé
        await repository.mark_completed(batch_id)
        log.info("worker.batch.completed", batch_id=str(batch_id))

    except Exception as exc:
        log.exception("worker.batch.failed", batch_id=str(batch_id), error=str(exc))
        await repository.mark_failed(batch_id, error_message=str(exc))