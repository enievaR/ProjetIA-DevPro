FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    HF_HOME=/app/.huggingface

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src /app/src

# torch CPU-only (beaucoup plus léger que le build CUDA par défaut)
RUN uv pip install --system --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu

# Dépendances du projet (transformers trouvera torch déjà installé)
RUN uv pip install --system --no-cache-dir -e .

# Pré-téléchargement du modèle de traduction (baked dans l'image, pas de réseau au runtime)
RUN python -c "\
from transformers import MarianMTModel, MarianTokenizer; \
MarianTokenizer.from_pretrained('Helsinki-NLP/opus-mt-fr-en'); \
MarianMTModel.from_pretrained('Helsinki-NLP/opus-mt-fr-en')"

COPY workflows /app/workflows

RUN useradd --uid 1000 --create-home --shell /bin/bash app \
    && mkdir -p /data/images \
    && chown -R app:app /app /data/images
USER app

CMD ["python", "-m", "src.worker.main"]
