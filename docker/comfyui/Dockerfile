FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Outils système nécessaires (git pour clone, curl pour healthcheck + téléchargement modèle)
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone ComfyUI (version pinnée pour reproductibilité)
# NOTE : pin à ajuster si besoin - on prend master pour le sprint 1
RUN git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git /app/ComfyUI

WORKDIR /app/ComfyUI

# Installation torch CPU + deps ComfyUI
# torch CPU-only (pas de CUDA) : plus léger, adapté au contexte école sans GPU
RUN pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        torch torchvision torchaudio \
    && pip install --no-cache-dir -r requirements.txt

# Script d'entrypoint : télécharge SD-Turbo si absent, puis lance ComfyUI
COPY docker/comfyui/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8188

ENTRYPOINT ["/entrypoint.sh"]