"""
Interface abstraite du backend d'inférence.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.common.models import GeneratedImage, PromptSpec


class InferenceBackend(ABC):

    @abstractmethod
    async def generate(self, spec: PromptSpec, count: int) -> list[GeneratedImage]:
        """Génère `count` images à partir de `spec`."""
        
    @abstractmethod
    async def health(self) -> bool:
        """Retourne True si le backend est prêt à recevoir des requêtes."""
        ...