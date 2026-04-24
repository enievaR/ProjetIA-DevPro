"""
Tables statiques de mapping pour la construction de prompts.
"""

from __future__ import annotations

from src.common.models import Ambiance, Cadrage, Style

# -----------------------------------------------------------------------------
# Préfixe qualité ajouté à tous les prompts
# -----------------------------------------------------------------------------
QUALITY_PREFIX = "high quality, detailed, masterpiece, sharp focus"

# -----------------------------------------------------------------------------
# Style → tags spécifiques
# -----------------------------------------------------------------------------
STYLE_TAGS: dict[Style, str] = {
    "anime": "anime style, 2d illustration, vibrant colors",
    "semi-realiste": "semi-realistic, detailed shading, soft details",
    "illustration": "digital illustration, vibrant colors, artistic",
    "peinture": "oil painting, brushstrokes visible, painterly",
}

# -----------------------------------------------------------------------------
# Ambiance → tags d'éclairage et atmosphère
# -----------------------------------------------------------------------------
AMBIANCE_TAGS: dict[Ambiance, str] = {
    "neutre": "balanced lighting, neutral tones",
    "douce": "soft lighting, warm tones, serene atmosphere",
    "dramatique": "cinematic lighting, high contrast, dramatic shadows",
    "mysterieuse": "misty, dim lighting, mysterious atmosphere, foggy",
}

# -----------------------------------------------------------------------------
# Cadrage → résolution (width, height)
# Résolutions natives SDXL (multiples de 64, ratio adapté)
# Source : https://stability.ai/learning-hub/stable-diffusion-3-prompt-guide
# -----------------------------------------------------------------------------
RESOLUTION_BY_CADRAGE: dict[Cadrage, tuple[int, int]] = {
    "portrait": (832, 1216),
    "carre": (1024, 1024),
    "paysage": (1216, 832),
}

# -----------------------------------------------------------------------------
# Negative prompt par défaut (toujours appliqué)
# -----------------------------------------------------------------------------
NEGATIVE_PROMPT_DEFAULT = (
    "lowres, bad anatomy, worst quality, blurry, deformed, ugly, "
    "low quality, jpeg artifacts, extra limbs, missing fingers"
)