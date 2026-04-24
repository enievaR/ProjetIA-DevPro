"""Handlers Gradio : la logique appelée par les composants UI.

Séparé de l'UI pour faciliter les tests et garder `main.py` lisible.
Tous les handlers sont async (Gradio supporte nativement asyncio).
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from src.common.config import get_settings
from src.common.logging import get_logger
from src.common.models import BatchRequest
from src.db import repository
from src.worker import enqueue_batch

log = get_logger(__name__)

# Le volume `./data/images` est monté en read-only dans le container Gradio.
# C'est aussi `output_dir` du backend, donc les chemins en DB sont relatifs à ça.
IMAGES_ROOT = Path("/data/images")


# =============================================================================
# Soumission d'un nouveau batch
# =============================================================================
async def submit_batch(
    subject: str, style: str, ambiance: str, cadrage: str, image_count: int
) -> tuple[str, str]:
    """Crée un batch en DB + push dans la queue.

    Retourne (batch_id_str, status_message) pour mise à jour de l'UI.
    """
    try:
        request = BatchRequest(
            subject=subject,
            style=style,  # type: ignore[arg-type]
            ambiance=ambiance,  # type: ignore[arg-type]
            cadrage=cadrage,  # type: ignore[arg-type]
            image_count=int(image_count),
        )
    except Exception as exc:
        log.warning("gradio.submit.invalid", error=str(exc))
        return "", f"❌ Requête invalide : {exc}"

    batch_id = await repository.create_batch(request)
    await enqueue_batch(batch_id)
    log.info("gradio.submit.queued", batch_id=str(batch_id))

    backend = get_settings().inference_backend
    estimate = (
        "quelques secondes"
        if backend == "mock"
        else f"environ {3 * request.image_count} minutes (CPU)"
    )

    return (
        str(batch_id),
        f"✅ Batch en cours (id `{batch_id}`)\n\nGénération en cours, "
        f"durée estimée : {estimate}.\n\nLa galerie se mettra à jour automatiquement.",
    )


# =============================================================================
# Polling : récupère l'état + les images d'un batch
# =============================================================================
async def poll_batch(batch_id_str: str) -> tuple[str, list[str]]:
    """Récupère l'état actuel d'un batch + les chemins absolus des images.

    Retourne (status_message, list_of_image_paths) pour Gradio.
    Si batch_id_str est vide ou invalide, retourne (vide, []).
    """
    if not batch_id_str:
        return "", []

    try:
        batch_id = UUID(batch_id_str)
    except ValueError:
        return "❌ ID de batch invalide", []

    batch = await repository.get_batch(batch_id)
    if batch is None:
        return f"❌ Batch `{batch_id_str}` introuvable", []

    images = await repository.get_images_for_batch(batch_id)
    image_paths = [str(IMAGES_ROOT / img.file_path) for img in images]

    state_label = {
        "queued": "⏳ En attente du worker",
        "processing": "⚙️ Génération en cours",
        "completed": f"✅ Terminé ({len(images)} images)",
        "failed": f"❌ Échec : {batch.error_message or 'erreur inconnue'}",
    }.get(batch.state, batch.state)

    return state_label, image_paths


# =============================================================================
# Historique des batches récents
# =============================================================================
async def list_recent() -> list[list[str]]:
    """Retourne les 10 derniers batches sous forme de tableau pour gr.Dataframe.

    Colonnes : Date, État, Sujet, Style, Images
    """
    batches = await repository.list_recent_batches(limit=10)
    rows: list[list[str]] = []
    for b in batches:
        rows.append(
            [
                b.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                b.state,
                (b.subject[:60] + "…") if len(b.subject) > 60 else b.subject,
                b.style,
                str(b.image_count),
            ]
        )
    return rows