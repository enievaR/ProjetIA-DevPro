"""Stub Gradio : affiche le formulaire, valide les inputs. Pas encore de génération."""

from __future__ import annotations

import gradio as gr

from src.common.config import get_settings
from src.common.logging import configure_logging, get_logger
from src.common.models import BatchRequest

settings = get_settings()
configure_logging(settings.log_level)
log = get_logger(__name__)


def submit_batch(subject: str, style: str, ambiance: str, cadrage: str) -> str:
    """Handler du bouton 'Générer'. Stub : valide et retourne un message."""
    try:
        request = BatchRequest(
            subject=subject,
            style=style,  # type: ignore[arg-type]
            ambiance=ambiance,  # type: ignore[arg-type]
            cadrage=cadrage,  # type: ignore[arg-type]
        )
    except Exception as exc:
        log.warning("batch.request.invalid", error=str(exc))
        return f"❌ Requête invalide : {exc}"

    log.info("batch.request.received", request=request.model_dump())
    return (
        f"✅ Requête reçue (stub, pas encore de génération)\n\n"
        f"- Sujet : {request.subject}\n"
        f"- Style : {request.style}\n"
        f"- Ambiance : {request.ambiance}\n"
        f"- Cadrage : {request.cadrage}\n"
        f"- Nombre d'images : {request.image_count}"
    )


def build_ui() -> gr.Blocks:
    """Construit l'interface Gradio."""
    with gr.Blocks(title="ProjetIA-DevPro") as demo:
        gr.Markdown("# ProjetIA-DevPro — Générateur d'images IA")
        gr.Markdown("*Sprint 1 : stub fonctionnel, pas encore de génération réelle.*")

        with gr.Row():
            with gr.Column(scale=2):
                subject = gr.Textbox(
                    label="Sujet",
                    placeholder="Ex. une femme rousse dans une forêt au coucher du soleil",
                    lines=2,
                )
                style = gr.Radio(
                    choices=["anime", "semi-realiste", "illustration", "peinture"],
                    value="anime",
                    label="Style",
                )
                ambiance = gr.Radio(
                    choices=["neutre", "douce", "dramatique", "mysterieuse"],
                    value="neutre",
                    label="Ambiance",
                )
                cadrage = gr.Radio(
                    choices=["portrait", "carre", "paysage"],
                    value="carre",
                    label="Cadrage",
                )
                submit_btn = gr.Button("Générer", variant="primary")

            with gr.Column(scale=3):
                output = gr.Markdown(label="Statut")

        submit_btn.click(
            fn=submit_batch,
            inputs=[subject, style, ambiance, cadrage],
            outputs=[output],
        )

    return demo


def main() -> None:
    log.info("gradio.starting", host=settings.gradio_host, port=settings.gradio_port)
    demo = build_ui()
    demo.launch(
        server_name=settings.gradio_host,
        server_port=settings.gradio_port,
        show_error=True,
    )


if __name__ == "__main__":
    main()