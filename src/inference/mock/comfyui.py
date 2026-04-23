"""Stub de ComfyUIBackend : appellera ComfyUI par HTTP au sprint 2."""

from __future__ import annotations

import httpx

from src.common.config import get_settings
from src.common.model import GeneratedImage, PromptSpec
from src.inference.base import InferenceBackend


class ComfyUIBackend(InferenceBackend):
    """Backend qui pilote un serveur ComfyUI distant via son API HTTP."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or get_settings().comfyui_url

    async def generate(self, spec: PromptSpec, count: int) -> list[GeneratedImage]:
        raise NotImplementedError("Implémenté au sprint 2")

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/system_stats")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False