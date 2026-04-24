"""Backends d'inférence d'images (interface + implémentations + factory)."""

from src.inference.base import InferenceBackend
from src.inference.comfyui import ComfyUIBackend, ComfyUIError
from src.inference.factory import get_backend
from src.inference.mock import MockBackend

__all__ = [
    "InferenceBackend",
    "ComfyUIBackend",
    "ComfyUIError",
    "MockBackend",
    "get_backend",
]