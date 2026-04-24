"""Factory du backend d'inférence.

Le worker appelle `get_backend()` au démarrage et obtient l'implémentation
concrète selon `INFERENCE_BACKEND` dans l'environnement.

Pour ajouter un nouveau backend (ex. `RunPodBackend` post-école) :
1. Créer la classe qui implémente `InferenceBackend`
2. Ajouter sa valeur dans le `Literal` de `Settings.inference_backend`
3. Ajouter une branche ici

Aucune autre modification du worker n'est nécessaire — c'est précisément
l'intérêt de l'inversion de dépendance.
"""

from __future__ import annotations

from src.common.config import get_settings
from src.common.logging import get_logger
from src.inference.base import InferenceBackend
from src.inference.comfyui import ComfyUIBackend
from src.inference.mock import MockBackend

log = get_logger(__name__)


def get_backend(workflow_path: str | None = None) -> InferenceBackend:
    """Retourne l'implémentation de InferenceBackend selon la config.

    Si `workflow_path` n'est pas fourni, utilise `settings.workflow_path`
    (configurable via la variable d'env WORKFLOW_PATH).
    """
    settings = get_settings()
    backend_name = settings.inference_backend
    wf_path = workflow_path or settings.workflow_path

    log.info("inference.factory.select", backend=backend_name, workflow=wf_path)

    if backend_name == "comfyui":
        return ComfyUIBackend(workflow_path=wf_path)
    if backend_name == "mock":
        return MockBackend()

    raise ValueError(f"Backend d'inférence inconnu : {backend_name}")