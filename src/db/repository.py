"""Repository : API métier de persistance pour les batches et images.

C'est le seul module qui contient du SQL. Tout le reste de l'app (worker,
gradio) appelle uniquement ces fonctions Python typées.

Convention : chaque fonction acquiert sa propre connexion depuis le pool.
Pour des opérations multi-statements atomiques, utiliser une transaction
explicite via `acquire_connection()` au niveau appelant.
"""

from __future__ import annotations

from uuid import UUID

from src.common.logging import get_logger
from src.common.models import (
    Batch,
    BatchRequest,
    GeneratedImage,
    Image,
)
from src.db.pool import acquire_connection

log = get_logger(__name__)


# =============================================================================
# Création / mise à jour d'état d'un batch
# =============================================================================


async def create_batch(request: BatchRequest) -> UUID:
    """Crée une nouvelle ligne dans `batches` (état = 'queued') et retourne son ID."""
    async with acquire_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO batches (subject, style, ambiance, cadrage, image_count, state)
            VALUES ($1, $2, $3, $4, $5, 'queued')
            RETURNING id
            """,
            request.subject,
            request.style,
            request.ambiance,
            request.cadrage,
            request.image_count,
        )
    batch_id = row["id"]
    log.info("db.batch.created", batch_id=str(batch_id), state="queued")
    return batch_id


async def mark_processing(batch_id: UUID, prompt_enriched: str, negative_prompt: str) -> None:
    """Marque le batch comme en cours de génération + stocke le prompt enrichi."""
    async with acquire_connection() as conn:
        await conn.execute(
            """
            UPDATE batches
            SET state = 'processing',
                prompt_enriched = $2,
                negative_prompt = $3,
                started_at = NOW()
            WHERE id = $1
            """,
            batch_id,
            prompt_enriched,
            negative_prompt,
        )
    log.info("db.batch.processing", batch_id=str(batch_id))


async def mark_completed(batch_id: UUID) -> None:
    """Marque le batch comme terminé avec succès."""
    async with acquire_connection() as conn:
        await conn.execute(
            """
            UPDATE batches
            SET state = 'completed',
                completed_at = NOW()
            WHERE id = $1
            """,
            batch_id,
        )
    log.info("db.batch.completed", batch_id=str(batch_id))


async def mark_failed(batch_id: UUID, error_message: str) -> None:
    """Marque le batch comme échoué + stocke le message d'erreur."""
    async with acquire_connection() as conn:
        await conn.execute(
            """
            UPDATE batches
            SET state = 'failed',
                error_message = $2,
                completed_at = NOW()
            WHERE id = $1
            """,
            batch_id,
            error_message,
        )
    log.warning("db.batch.failed", batch_id=str(batch_id), error=error_message)


# =============================================================================
# Ajout d'une image
# =============================================================================


async def add_image(batch_id: UUID, generated: GeneratedImage) -> UUID:
    """Insère une image générée et retourne son ID."""
    async with acquire_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO images (batch_id, seed, file_path, width, height)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            batch_id,
            generated.seed,
            generated.file_path,
            generated.width,
            generated.height,
        )
    image_id = row["id"]
    log.debug("db.image.added", image_id=str(image_id), batch_id=str(batch_id), seed=generated.seed)
    return image_id


# =============================================================================
# Lectures
# =============================================================================


async def get_batch(batch_id: UUID) -> Batch | None:
    """Récupère un batch par son ID, ou None s'il n'existe pas."""
    async with acquire_connection() as conn:
        row = await conn.fetchrow("SELECT * FROM batches WHERE id = $1", batch_id)
    if row is None:
        return None
    return Batch.model_validate(dict(row))


async def list_recent_batches(limit: int = 20) -> list[Batch]:
    """Retourne les N derniers batches, triés par date décroissante."""
    async with acquire_connection() as conn:
        rows = await conn.fetch(
            "SELECT * FROM batches ORDER BY created_at DESC LIMIT $1",
            limit,
        )
    return [Batch.model_validate(dict(row)) for row in rows]


async def get_images_for_batch(batch_id: UUID) -> list[Image]:
    """Retourne toutes les images d'un batch, triées par seed."""
    async with acquire_connection() as conn:
        rows = await conn.fetch(
            "SELECT * FROM images WHERE batch_id = $1 ORDER BY seed ASC",
            batch_id,
        )
    return [Image.model_validate(dict(row)) for row in rows]