"""Interface abstraite du backend d'inférence.

C'est le pattern architectural central du projet : le worker ne dépend que de
cette interface, jamais d'une implémentation concrète. Remplacer ComfyUI par
un backend distant (RunPod, Replicate, etc.) se fait par une nouvelle classe
implémentant `InferenceBackend`, sans toucher au reste.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.common.model import GeneratedImage, PromptSpec


class InferenceBackend(ABC):
    """Contrat que tout moteur d'inférence doit respecter."""

    @abstractmethod
    async def generate(self, spec: PromptSpec, count: int) -> list[GeneratedImage]:
        """Génère `count` images à partir de `spec`.

        Chaque image doit avoir un seed distinct (typiquement `spec.seed_start + i`).
        Le backend est responsable d'écrire le fichier sur disque et de retourner
        le chemin relatif dans `GeneratedImage.file_path`.
        """
        ...

    @abstractmethod
    async def health(self) -> bool:
        """Retourne True si le backend est prêt à recevoir des requêtes."""
        ...