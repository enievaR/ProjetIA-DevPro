#!/usr/bin/env bash
set -euo pipefail

MODELS_DIR="/app/ComfyUI/models/checkpoints"
MODEL_FILE="sd_turbo.safetensors"
MODEL_URL="https://huggingface.co/stabilityai/sd-turbo/resolve/main/sd_turbo.safetensors"

mkdir -p "${MODELS_DIR}"

if [[ ! -f "${MODELS_DIR}/${MODEL_FILE}" ]]; then
    echo "[entrypoint] SD-Turbo absent, téléchargement en cours..."
    curl -fL --retry 3 -o "${MODELS_DIR}/${MODEL_FILE}" "${MODEL_URL}"
    echo "[entrypoint] Téléchargement terminé."
else
    echo "[entrypoint] SD-Turbo déjà présent, on skip le téléchargement."
fi

echo "[entrypoint] Démarrage de ComfyUI sur 0.0.0.0:8188 (CPU)"
exec python main.py --listen 0.0.0.0 --port 8188 --cpu