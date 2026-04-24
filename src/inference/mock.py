"""Backend d'inférence mock : génère des images placeholder instantanément.

Utilisations :
- Dev rapide sans attendre ComfyUI (~3 min CPU vs ~50 ms mock)
- Tests unitaires (CI sans GPU)
- Démo de secours en soutenance si ComfyUI plante

Implémente strictement la même interface `InferenceBackend` que `ComfyUIBackend`,
ce qui démontre concrètement le pattern d'inversion de dépendance.

Les images générées sont des PNG 512×512 (ou autre selon spec) avec :
- Un fond de couleur dérivé du seed (déterministe)
- Le prompt et le seed inscrits en texte
"""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from pathlib import Path

from PIL import Image, ImageDraw

from src.common.logging import get_logger
from src.common.models import GeneratedImage, PromptSpec
from src.inference.base import InferenceBackend

log = get_logger(__name__)


class MockBackend(InferenceBackend):
    """Backend de test qui retourne des images placeholder PIL."""

    # Latence simulée pour rester réaliste sans bloquer (50ms par image)
    SIMULATED_LATENCY_SECONDS = 0.05

    def __init__(self, output_dir: str | Path = "/data/images") -> None:
        self.output_dir = Path(output_dir)
        log.info("mock_backend.init", output_dir=str(self.output_dir))

    async def health(self) -> bool:
        """Toujours healthy : le mock n'a aucune dépendance externe."""
        return True

    async def generate(self, spec: PromptSpec, count: int) -> list[GeneratedImage]:
        sub_dir = self.output_dir / f"batch-{spec.seed_start}-{uuid.uuid4().hex[:8]}"
        sub_dir.mkdir(parents=True, exist_ok=True)

        results: list[GeneratedImage] = []
        for i in range(count):
            seed = spec.seed_start + i
            await asyncio.sleep(self.SIMULATED_LATENCY_SECONDS)

            local_path = sub_dir / f"{seed}.png"
            self._render_placeholder(local_path, spec, seed)

            relative_path = str(local_path.relative_to(self.output_dir))
            results.append(
                GeneratedImage(
                    seed=seed,
                    file_path=relative_path,
                    width=spec.width,
                    height=spec.height,
                )
            )
            log.info("mock_backend.generated", seed=seed, file_path=relative_path)

        return results

    # -------------------------------------------------------------------------
    # Génération d'image placeholder
    # -------------------------------------------------------------------------
    @staticmethod
    def _render_placeholder(path: Path, spec: PromptSpec, seed: int) -> None:
        """Crée un PNG avec un fond coloré déterministe et du texte explicatif."""
        # Couleur de fond dérivée du seed (déterministe)
        seed_hash = hashlib.md5(str(seed).encode()).hexdigest()
        r = int(seed_hash[0:2], 16)
        g = int(seed_hash[2:4], 16)
        b = int(seed_hash[4:6], 16)

        img = Image.new("RGB", (spec.width, spec.height), (r, g, b))
        draw = ImageDraw.Draw(img)

        # Texte du prompt tronqué + seed
        max_chars_per_line = max(20, spec.width // 12)
        truncated_prompt = spec.prompt[:200]
        wrapped = MockBackend._wrap(truncated_prompt, max_chars_per_line)

        text_y = 20
        draw.text((20, text_y), f"MOCK IMAGE", fill="white")
        draw.text((20, text_y + 20), f"seed: {seed}", fill="white")
        draw.text((20, text_y + 40), f"size: {spec.width}x{spec.height}", fill="white")
        draw.text((20, text_y + 70), wrapped, fill="white")

        img.save(path, format="PNG")

    @staticmethod
    def _wrap(text: str, width: int) -> str:
        """Wrap minimal sans dépendance (pas de textwrap import nécessaire ici)."""
        lines: list[str] = []
        current = ""
        for word in text.split():
            if len(current) + len(word) + 1 > width:
                lines.append(current)
                current = word
            else:
                current = f"{current} {word}".strip()
        if current:
            lines.append(current)
        return "\n".join(lines)