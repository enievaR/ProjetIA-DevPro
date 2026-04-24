"""Construction de l'UI Gradio.

Trois zones :
- Formulaire de soumission (gauche)
- Galerie + statut du batch courant (droite)
- Historique des derniers batches (en bas)

Le polling de l'état se fait via gr.Timer qui appelle poll_batch() toutes
les 2 secondes. L'historique est rafraîchi toutes les 10 secondes.
"""

from __future__ import annotations

import gradio as gr

from src.gradio_app.handlers import list_recent, poll_batch, submit_batch

POLL_INTERVAL_SECONDS = 2.0
HISTORY_REFRESH_SECONDS = 10.0


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="ProjetIA-DevPro") as demo:
        gr.Markdown("# 🎨 ProjetIA-DevPro — Générateur d'images IA")
        gr.Markdown(
            "Décris ce que tu veux voir, choisis un style, une ambiance et un cadrage. "
            "Le bot s'occupe du reste."
        )

        # État courant du batch (caché, sert de mémoire entre soumission et polling)
        current_batch_id = gr.State(value="")

        with gr.Row():
            # ─── Colonne formulaire ──────────────────────────────────────────
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
                    value="douce",
                    label="Ambiance",
                )
                cadrage = gr.Radio(
                    choices=["portrait", "carre", "paysage"],
                    value="carre",
                    label="Cadrage",
                )
                image_count = gr.Slider(
                    minimum=1, maximum=4, step=1, value=2,
                    label="Nombre d'images",
                )
                submit_btn = gr.Button("✨ Générer", variant="primary", size="lg")

            # ─── Colonne galerie + statut ───────────────────────────────────
            with gr.Column(scale=3):
                status = gr.Markdown("*Aucune génération en cours.*")
                gallery = gr.Gallery(
                    label="Images générées",
                    columns=2,
                    height="auto",
                    object_fit="contain",
                )

        # ─── Bas : historique ───────────────────────────────────────────────
        gr.Markdown("## 📜 Historique récent")
        history_table = gr.Dataframe(
            headers=["Date", "État", "Sujet", "Style", "Images"],
            datatype=["str", "str", "str", "str", "str"],
            interactive=False,
        )

        # ─── Câblage : soumission ───────────────────────────────────────────
        submit_btn.click(
            fn=submit_batch,
            inputs=[subject, style, ambiance, cadrage, image_count],
            outputs=[current_batch_id, status],
        )

        # ─── Câblage : polling de l'état (toutes les 2s) ────────────────────
        poll_timer = gr.Timer(value=POLL_INTERVAL_SECONDS)
        poll_timer.tick(
            fn=poll_batch,
            inputs=[current_batch_id],
            outputs=[status, gallery],
        )

        # ─── Câblage : refresh de l'historique (toutes les 10s + au chargement) ─
        history_timer = gr.Timer(value=HISTORY_REFRESH_SECONDS)
        history_timer.tick(fn=list_recent, outputs=[history_table])
        demo.load(fn=list_recent, outputs=[history_table])

    return demo