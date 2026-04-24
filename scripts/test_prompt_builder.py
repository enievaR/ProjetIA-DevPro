"""Test isolé du prompt_builder.

Usage :
    docker compose exec worker python -m scripts.test_prompt_builder

Affiche le prompt construit pour quelques combinaisons de paramètres.
Pas besoin de Postgres/Redis/ComfyUI pour ce test.
"""

from __future__ import annotations

from src.common.models import BatchRequest
from src.prompt_builder import build


def show(name: str, request: BatchRequest) -> None:
    spec = build(request, seed_start=42)
    print(f"\n--- {name} ---")
    print(f"Prompt    : {spec.prompt}")
    print(f"Negative  : {spec.negative_prompt}")
    print(f"Resolution: {spec.width}x{spec.height}")
    print(f"Seed start: {spec.seed_start}")


def main() -> None:
    show(
        "Anime / douce / portrait",
        BatchRequest(
            subject="une femme rousse dans une forêt au coucher du soleil",
            style="anime",
            ambiance="douce",
            cadrage="portrait",
        ),
    )

    show(
        "Peinture / dramatique / paysage",
        BatchRequest(
            subject="un château médiéval sur une falaise pendant un orage",
            style="peinture",
            ambiance="dramatique",
            cadrage="paysage",
        ),
    )

    show(
        "Illustration / mysterieuse / carre",
        BatchRequest(
            subject="a cyberpunk alley at night with neon signs",
            style="illustration",
            ambiance="mysterieuse",
            cadrage="carre",
            image_count=2,
        ),
    )


if __name__ == "__main__":
    main()