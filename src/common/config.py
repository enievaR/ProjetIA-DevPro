"""Configuration chargé depuis env"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel


class Settings(BaseModel):
    """Déclaration des variable de configuration"""

    # Postgres
    postgres_user: str = "projetia"
    postgres_password: str = "changeme"
    postgres_db: str = "projetia"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379

    # ComfyUI
    comfyui_host: str = "comfyui"
    comfyui_port: int = 8188

    # Gradio
    gradio_host: str = "0.0.0.0"
    gradio_port: int = 7860

    # Inférence
    inference_backend: Literal["comfyui", "mock"] = "comfyui"
    batch_size: int = 4

    # Logs
    log_level: str = "INFO"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def comfyui_url(self) -> str:
        return f"http://{self.comfyui_host}:{self.comfyui_port}"


@lru_cache
def get_settings() -> Settings:
    """Chargement des variables depuis env"""
    return Settings(
        postgres_user=os.getenv("POSTGRES_USER", "projetia"),
        postgres_password=os.getenv("POSTGRES_PASSWORD", "changeme"),
        postgres_db=os.getenv("POSTGRES_DB", "projetia"),
        postgres_host=os.getenv("POSTGRES_HOST", "postgres"),
        postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
        redis_host=os.getenv("REDIS_HOST", "redis"),
        redis_port=int(os.getenv("REDIS_PORT", "6379")),
        comfyui_host=os.getenv("COMFYUI_HOST", "comfyui"),
        comfyui_port=int(os.getenv("COMFYUI_PORT", "8188")),
        gradio_host=os.getenv("GRADIO_HOST", "0.0.0.0"),
        gradio_port=int(os.getenv("GRADIO_PORT", "7860")),
        inference_backend=os.getenv("INFERENCE_BACKEND", "comfyui"),  # type: ignore[arg-type]
        batch_size=int(os.getenv("BATCH_SIZE", "4")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )