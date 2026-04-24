"""Entrypoint du service Gradio.

Le pool DB est init paresseusement à la première requête (dans la même
event loop que celle gérée par Gradio).
"""

from __future__ import annotations

import os

import gradio as gr

# Désactive la télémétrie Gradio AVANT l'import des composants
# (Gradio 6.0+ ne supporte plus analytics_enabled= dans launch())
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

from src.common.config import get_settings  # noqa: E402
from src.common.logging import configure_logging, get_logger  # noqa: E402
from src.gradio_app.ui import build_ui  # noqa: E402

settings = get_settings()
configure_logging(settings.log_level)
log = get_logger(__name__)


def main() -> None:
    log.info(
        "gradio.starting",
        host=settings.gradio_host,
        port=settings.gradio_port,
        backend=settings.inference_backend,
    )

    demo = build_ui()
    demo.queue()
    demo.launch(
        server_name=settings.gradio_host,
        server_port=settings.gradio_port,
        show_error=True,
        theme=gr.themes.Soft(),
        allowed_paths=["/data/images"],
    )


if __name__ == "__main__":
    main()