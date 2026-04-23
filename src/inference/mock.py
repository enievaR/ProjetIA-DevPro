"""Stub de MockBackend : utilisé pour les tests et le dev rapide.

Sera implémenté au sprint 2 (retourne des images placeholder sans inférence).
"""

from __future__ import annotations

from src.common.model import GeneratedImage, PromptSpec
from src.inference.base import InferenceBackend


class MockBackend(InferenceBackend):
    """Backend de test qui retourne des images placeholder."""

    async def generate(self, spec: PromptSpec, count: int) -> list[GeneratedImage]:
        raise NotImplementedError("Implémenté au sprint 2")

    async def health(self) -> bool:
        return True