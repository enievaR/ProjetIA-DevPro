"""Contrats d'interface entre les services."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# Enums (en Literal pour la simplicité + validation Pydantic)
# -----------------------------------------------------------------------------
Style = Literal["anime", "semi-realiste", "illustration", "peinture"]
Ambiance = Literal["neutre", "douce", "dramatique", "mysterieuse"]
Cadrage = Literal["portrait", "carre", "paysage"]
BatchState = Literal["queued", "processing", "completed", "failed"]


# -----------------------------------------------------------------------------
# Entrée utilisateur (soumis via Gradio)
# -----------------------------------------------------------------------------
class BatchRequest(BaseModel):
    """Requête de génération, construite côté Gradio à partir du formulaire."""

    subject: str = Field(min_length=1, max_length=500)
    style: Style
    ambiance: Ambiance
    cadrage: Cadrage
    image_count: int = Field(default=4, ge=1, le=15)


# -----------------------------------------------------------------------------
# Spec de prompt passée à l'InferenceBackend
# -----------------------------------------------------------------------------
class PromptSpec(BaseModel):
    """Prompt complet prêt à être envoyé au moteur d'inférence."""

    prompt: str
    negative_prompt: str
    width: int
    height: int
    seed_start: int


# -----------------------------------------------------------------------------
# Image générée retournée par l'InferenceBackend
# -----------------------------------------------------------------------------
class GeneratedImage(BaseModel):
    """Une image produite par le backend d'inférence."""

    seed: int
    file_path: str  # chemin relatif à /data/images
    width: int
    height: int


# -----------------------------------------------------------------------------
# Enregistrements DB (lecture)
# -----------------------------------------------------------------------------
class Batch(BaseModel):
    """Représentation d'une ligne de la table `batches`."""

    id: UUID
    subject: str
    style: Style
    ambiance: Ambiance
    cadrage: Cadrage
    prompt_enriched: str | None
    negative_prompt: str | None
    image_count: int
    state: BatchState
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class Image(BaseModel):
    """Représentation d'une ligne de la table `images`."""

    id: UUID
    batch_id: UUID
    seed: int
    file_path: str
    width: int | None
    height: int | None
    created_at: datetime


# -----------------------------------------------------------------------------
# Payload de job Redis
# -----------------------------------------------------------------------------
class JobPayload(BaseModel):
    """Ce qui est poussé dans Redis pour qu'un worker dépile."""

    batch_id: UUID