"""Construction du prompt enrichi à partir d'une BatchRequest.

Pipeline :

    BatchRequest
        │
        ▼
    [QUALITY_PREFIX] + [STYLE_TAGS[style]] + [AMBIANCE_TAGS[ambiance]] + [subject]
        │
        ▼
    PromptSpec(prompt, negative_prompt, width, height, seed_start)
"""

from __future__ import annotations

from src.common.models import BatchRequest, PromptSpec
from src.prompt_builder.mappings import (
    AMBIANCE_TAGS,
    NEGATIVE_PROMPT_DEFAULT,
    QUALITY_PREFIX,
    RESOLUTION_BY_CADRAGE,
    STYLE_TAGS,
)


def build(request: BatchRequest, seed_start: int) -> PromptSpec:
    """Transforme une requête utilisateur en spec de prompt prête pour l'inférence.

    Les éléments sont concaténés dans cet ordre :
    1. Préfixe qualité (constant)
    2. Tags du style choisi
    3. Tags de l'ambiance choisie
    4. Sujet brut tapé par l'utilisateur

    Le sujet est conservé tel quel (pas de traduction FR→EN ici, c'est prévu
    pour une phase future).
    """
    parts = [
        QUALITY_PREFIX,
        STYLE_TAGS[request.style],
        AMBIANCE_TAGS[request.ambiance],
        request.subject.strip(),
    ]
    prompt = ", ".join(part for part in parts if part)

    width, height = RESOLUTION_BY_CADRAGE[request.cadrage]

    return PromptSpec(
        prompt=prompt,
        negative_prompt=NEGATIVE_PROMPT_DEFAULT,
        width=width,
        height=height,
        seed_start=seed_start,
    )