"""Traduction FR→EN du sujet utilisateur avant enrichissement du prompt.

Le modèle Helsinki-NLP/opus-mt-fr-en est chargé une fois au startup du worker
(via load()) et réutilisé pour tous les jobs. Si le chargement ou la traduction
échoue, le texte original est retourné sans lever d'exception.
"""

from __future__ import annotations

from src.common.logging import get_logger

log = get_logger(__name__)

_MODEL_NAME = "Helsinki-NLP/opus-mt-fr-en"

_tokenizer = None
_model = None


def load() -> None:
    """Charge le modèle de traduction. Appelé une fois au startup du worker."""
    global _tokenizer, _model

    # Import différé : torch + transformers sont lourds, on ne les charge
    # que si le worker démarre (pas lors des imports dans les tests unitaires).
    from transformers import MarianMTModel, MarianTokenizer  # noqa: PLC0415

    log.info("translator.loading", model=_MODEL_NAME)
    _tokenizer = MarianTokenizer.from_pretrained(_MODEL_NAME)
    _model = MarianMTModel.from_pretrained(_MODEL_NAME)
    log.info("translator.ready")


def translate(text: str) -> str:
    """Traduit un texte FR→EN. Retourne le texte original en cas d'erreur."""
    if _tokenizer is None or _model is None:
        log.warning("translator.not_loaded")
        return text

    try:
        tokens = _tokenizer(
            [text],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        )
        translated_ids = _model.generate(**tokens)
        result = _tokenizer.decode(translated_ids[0], skip_special_tokens=True)
        log.debug("translator.done", original=text[:60], translated=result[:60])
        return result
    except Exception as exc:
        log.warning("translator.error", error=str(exc))
        return text
